import sys
import os
import io
import argparse
import concurrent.futures
import time
import gc 
import logging
from functools import partial
from dataclasses import dataclass
from typing import Tuple

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')

try:
    import fitz
except ImportError:
    logging.error("PyMuPDF not found. Install with: pip install pymupdf")
    sys.exit(1)
try:
    from PIL import Image, ImageEnhance
except ImportError:
    logging.error("Pillow not found. Install with: pip install Pillow")
    sys.exit(1)
try:
    import numpy as np
except ImportError:
    logging.error("NumPy not found. Install with: pip install numpy")
    sys.exit(1)
try:
    from tqdm import tqdm
except ImportError:
    def tqdm(iterable, *args, **kwargs):
        return iterable
    logging.warning("tqdm not found. Install with: pip install tqdm to see a progress bar.")

@dataclass
class ProcessingConfig:
    bg_color: Tuple[int, int, int]
    text_color: Tuple[int, int, int]
    color_threshold: float
    contrast_boost: float
    bright_bg_threshold: float
    dark_text_threshold: float
    zoom: float
    photo_threshold: float = 0.85

def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    hex_color = hex_color.lstrip('#')
    if len(hex_color) != 6 or not all(c in '0123456789abcdefABCDEF' for c in hex_color):
        raise ValueError("Invalid hex color format. Use #RRGGBB.")
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def rgb_to_luminance(r: np.ndarray, g: np.ndarray, b: np.ndarray) -> np.ndarray:
    return 0.299 * r + 0.587 * g + 0.114 * b

def _apply_monochrome_inversion(arr: np.ndarray, inversion_mask: np.ndarray, luminance: np.ndarray, config: ProcessingConfig):
    if not np.any(inversion_mask): return
    flat_indices = np.where(inversion_mask.ravel())[0]
    arr_view = arr.reshape(-1, 3)
    mono_luminance = luminance[inversion_mask].ravel()
    is_bright_bg = mono_luminance >= config.bright_bg_threshold
    is_dark_text = mono_luminance <= config.dark_text_threshold
    is_midtone = ~is_bright_bg & ~is_dark_text
    bg_array = np.array(config.bg_color, dtype=np.float32)
    text_array = np.array(config.text_color, dtype=np.float32)
    if np.any(is_bright_bg):
        arr_view[flat_indices[is_bright_bg]] = bg_array
    if np.any(is_dark_text):
        arr_view[flat_indices[is_dark_text]] = text_array
    if np.any(is_midtone):
        midtone_indices = flat_indices[is_midtone]
        mid_luminance = mono_luminance[is_midtone]
        inverted_luminance = 255.0 - mid_luminance
        normalized_inv = inverted_luminance / 255.0
        channel_range = text_array - bg_array
        scaled_colors = bg_array + normalized_inv[:, np.newaxis] * channel_range
        arr_view[midtone_indices] = scaled_colors
    del flat_indices, arr_view, mono_luminance
    gc.collect()

def process_image_data(img_array: np.ndarray, config: ProcessingConfig) -> Image.Image:
    chroma = np.max(img_array, axis=2) - np.min(img_array, axis=2)
    if np.mean(chroma >= config.color_threshold) >= config.photo_threshold:
        return Image.fromarray(img_array.astype(np.uint8))
    arr = img_array.astype(np.float32)
    r, g, b = arr[..., 0], arr[..., 1], arr[..., 2]
    luminance = rgb_to_luminance(r, g, b)
    inversion_mask = ~(np.max(arr, axis=2) - np.min(arr, axis=2) >= config.color_threshold)
    _apply_monochrome_inversion(arr, inversion_mask, luminance, config)
    del r, g, b, luminance, inversion_mask
    arr = np.clip(arr, 0, 255)
    processed_img = Image.fromarray(arr.astype(np.uint8))
    if config.contrast_boost > 1.0:
        enhancer = ImageEnhance.Contrast(processed_img)
        processed_img = enhancer.enhance(config.contrast_boost)
    return processed_img

def process_page_worker(page_num: int, pixmap_data: bytes, pixmap_width: int, pixmap_height: int, rect: fitz.Rect, config: ProcessingConfig):
    try:
        if pixmap_data is None:
            logging.warning(f"Page {page_num + 1} was skipped due to a rendering failure.")
            return page_num, None, None
        img = Image.frombytes("RGB", (pixmap_width, pixmap_height), pixmap_data)
        img_array = np.array(img)
        del img
        processed_img = process_image_data(img_array, config)
        del img_array
        img_bytes = io.BytesIO()
        processed_img.save(img_bytes, format="JPEG", quality=95, optimize=True)
        img_bytes.seek(0)
        result_data = img_bytes.getvalue()
        del img_bytes, processed_img
        return page_num, result_data, rect
    except Exception as e:
        logging.error(f"Page {page_num + 1} failed during processing: {e}")
        return page_num, None, None
    finally:
        gc.collect()
def create_dark_mode_pdf():
    parser = argparse.ArgumentParser(
        description="The Final PDF Dark Mode Converter",
        formatter_class=argparse.RawTextHelpFormatter
    )

    required = parser.add_argument_group('Required arguments')
    required.add_argument("input", help="Input PDF file path")
    
    output_opts = parser.add_argument_group('Output options')
    output_opts.add_argument("-o", "--output", help="Output PDF file path (default: input_dark.pdf)")
    output_opts.add_argument("-f", "--force", action="store_true", help="Overwrite output file if it exists")
    
    quality = parser.add_argument_group('Quality settings')
    quality.add_argument("-z", "--zoom", type=float, default=4.0, help="DPI zoom factor. Default: 4.0")
    quality.add_argument("-bg", "--background", type=str, default="#1E1E1E", help="Target background color. Default: #1E1E1E")
    quality.add_argument("-tc", "--text-color", type=str, default="#E0E0E0", help="Target text color. Default: #E0E0E0")
    quality.add_argument("-c", "--contrast", type=float, default=1.1, help="Final contrast boost. Default: 1.1")
    
    color_handling = parser.add_argument_group('Color handling')
    color_handling.add_argument("-ct", "--color-threshold", type=float, default=30, help="Color preservation threshold. Default: 30")
    
    advanced = parser.add_argument_group('Advanced thresholds')
    advanced.add_argument("--bright-bg", type=float, default=240, help="Luminance to treat as pure background. Default: 240")
    advanced.add_argument("--dark-text", type=float, default=50, help="Luminance to treat as pure text. Default: 50")
    advanced.add_argument("--photo-threshold", type=float, default=0.85, help="Fraction of page considered photo to skip processing. Default: 0.85")
    
    performance = parser.add_argument_group('Performance')
    performance.add_argument("--batch-size", type=int, default=50, help="Pages per memory batch. Default: 50")
    performance.add_argument("-j", "--jobs", type=int, default=os.cpu_count(), help="Parallel workers. Default: all CPU cores")
    
    args = parser.parse_args()

    if not os.path.exists(args.input):
        logging.error(f"Input file not found: '{args.input}'")
        sys.exit(1)
        
    output_path = args.output
    if not output_path:
        base, ext = os.path.splitext(args.input)
        output_path = f"{base}_dark{ext}"
        
    if os.path.exists(output_path) and not args.force:
        logging.error(f"Output file '{output_path}' exists. Use -f to overwrite.")
        sys.exit(1)
        
    try:
        bg_color_rgb = hex_to_rgb(args.background)
        text_color_rgb = hex_to_rgb(args.text_color)
    except ValueError as e:
        logging.error(f"Color parsing failed: {e}")
        sys.exit(1)

    config = ProcessingConfig(
        bg_color=bg_color_rgb, text_color=text_color_rgb, 
        color_threshold=args.color_threshold,
        contrast_boost=args.contrast, 
        bright_bg_threshold=args.bright_bg, 
        dark_text_threshold=args.dark_text, 
        zoom=args.zoom,
        photo_threshold=args.photo_threshold
    )
    
    try:
        source_doc_test = fitz.open(args.input)
        total_pages = len(source_doc_test)
        source_doc_test.close()
    except Exception as e:
        logging.error(f"Failed to open or read input PDF: {e}")
        sys.exit(1)

    logging.info(f"Converting '{args.input}' -> '{output_path}' ({total_pages} pages)")
    logging.info(f"Using config -> Zoom: {config.zoom}, BG: {args.background}, Text: {args.text_color}, Photo threshold: {config.photo_threshold}")

    output_doc = fitz.open()
    start_time = time.time()
    
    worker_func = partial(process_page_worker, config=config)
    
    with tqdm(total=total_pages, desc="Processing", unit="pg") as pbar:
        for batch_start in range(0, total_pages, args.batch_size):
            batch_end = min(batch_start + args.batch_size, total_pages)
            batch_range = range(batch_start, batch_end)
            
            batch_data = []
            doc_batch_open = fitz.open(args.input)
            mat = fitz.Matrix(config.zoom, config.zoom)
            
            for page_num in batch_range:
                try:
                    page = doc_batch_open[page_num]
                    rect = page.rect
                    pix = page.get_pixmap(matrix=mat, alpha=False, colorspace=fitz.csRGB)
                    if pix.samples is None:
                        batch_data.append((page_num, None, 0, 0, rect))
                    else:
                        batch_data.append((page_num, pix.samples, pix.width, pix.height, rect))
                except Exception as e:
                    logging.warning(f"Batch render failed for page {page_num + 1}: {e}")
                    batch_data.append((page_num, None, 0, 0, page.rect if 'page' in locals() else fitz.Rect(0,0,595,842)))
                finally:
                    if 'page' in locals(): del page
                    if 'pix' in locals(): del pix
                    if 'rect' in locals(): del rect
            
            doc_batch_open.close()
            del doc_batch_open, mat
            
            with concurrent.futures.ProcessPoolExecutor(max_workers=args.jobs) as executor:
                results = executor.map(
                    worker_func, 
                    [d[0] for d in batch_data],
                    [d[1] for d in batch_data],
                    [d[2] for d in batch_data],
                    [d[3] for d in batch_data],
                    [d[4] for d in batch_data]
                )
                
                temp_buffer = {}
                for page_num, data, rect in results:
                    if data and rect:
                        temp_buffer[page_num] = (data, rect)
                    pbar.update(1)

            for i in sorted(temp_buffer.keys()):
                data, rect = temp_buffer[i]
                page = output_doc.new_page(width=rect.width, height=rect.height)
                page.insert_image(rect, stream=data, keep_proportion=False)

            del temp_buffer, batch_data, results
            gc.collect()
                    
    logging.info("Saving final PDF...")
    output_doc.save(output_path, garbage=4, deflate=True, clean=True)
    output_doc.close()

    total_time = time.time() - start_time
    logging.info(f"Done! Created '{output_path}' in {total_time:.2f} seconds.")

def main():
    create_dark_mode_pdf()

if __name__ == "__main__":
    main()