# colorchangerPDF
Many existing tools on the website or Google extensions either don’t work or require you to upload your PDFs to a server, something I don’t trust with personal files. So, I created colorchangerPDF, a Python tool that lets you convert any PDF to a dark mode version, safely on your own machine.
if u like my project u should consider star it <3

Requirements 
##  Installation on your computer 

```
Install via pip:
```
```
pip install colorchangerPDF
```
OR 
```
pip3 install colorchangerPDF
```


How to use and what is the settings of the pip usage


colorchangerPDF /path/to/input.pdf -o /path/to/output.pdf
/path/to/input.pdf → the PDF file you want to convert. This can be:
```
showcase Mac: ~/Downloads/yourfile.pdf or /Users/username/Documents/yourfile.pdf

showcase Windows: C:\Users\YourName\Downloads\yourfile.pdf

showcase Linux: ~/Downloads/yourfile.pdf
```
```
/path/to/output.pdf → the converted dark mode PDF file 

~/Downloads/output.pdf

C:\Users\YourName\Documents\output.pdf
```
How i use on my computer 
```
colorchangerPDF ~/Downloads/qubit.pdf -o ~/Downloads/qubit_dark.pdf
```
NOTE you should change the input.pdf to how it saved on your computer and for output.pdf you should pick the name something non existed file


**HOW to change the settings with your desire.**

<img width="506" height="277" alt="Screenshot 2025-10-19 at 15 49 00" src="https://github.com/user-attachments/assets/2f560e7e-91f4-48d5-aeed-a9e865e776cf" />


here is a example of conversion 

**Original pdf** 

<img width="678" height="569" alt="Screenshot 2025-10-19 at 16 04 39" src="https://github.com/user-attachments/assets/2bcba79b-0f6d-43e1-a723-c1a9b11a2ff0" />


**Converted PDF**

<img width="678" height="569" alt="Screenshot 2025-10-19 at 16 02 07" src="https://github.com/user-attachments/assets/605280f8-b840-486b-bb1b-33479c3407b6" />




**Example Terminal Run**

<img width="567" height="109" alt="Screenshot 2025-10-19 at 15 55 14" src="https://github.com/user-attachments/assets/b71be267-ca8e-49ff-a04b-d9fd58c849ea" />

<img width="562" height="162" alt="Screenshot 2025-10-19 at 15 57 32" src="https://github.com/user-attachments/assets/7d19257a-181d-4a4d-9e0c-4d14252ffd88" />


**Common issue and How to fix them**


**common issue**
```
If you see this error when running colorchangerPDF:
```
```
Traceback (most recent call last):
  File "/opt/homebrew/bin/colorchangerPDF", line 3, in <module>
    from colorchangerPDF.script import main
ModuleNotFoundError: No module named 'colorchangerPDF'
```
**how to fix**
**The CLI script might be using a different Python environment. Reinstall the package using the Python interpreter that the CLI uses**
```
/opt/homebrew/opt/python@3.11/bin/python3.11 -m pip install --force-reinstall colorchangerPDF
```

then run colorchangerPDF
if it is not still working
If still not working, manually run
```
python3 -m colorchangerPDF.script
```

To check if the package is installed
```
pip show colorchangerPDF
```

if it say NOT FOUND run this command 
```
/opt/homebrew/opt/python@3.11/bin/python3.11 -m pip install --force-reinstall colorchangerPDF
```
