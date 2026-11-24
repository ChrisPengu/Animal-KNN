# Animal K-NN

<!-- impeccable:product-schema 1 -->

## Platform
windows

## Stack
Python 3.10, Tkinter/ttk Windows application and scikit-learn K-NN with Torchvision feature extraction. Launch from source with run-desktop.bat. No browser or web server.

## Users
Vietnamese students presenting and reviewing an image-processing and computer-vision project on a desktop computer.

## Product Purpose
Open one animal photograph, classify it into six groups, and understand the result through nearest training examples.

## Capabilities and Constraints
Bird, cat, deer, dog, horse and monkey. K-NN is the final classifier. CNNs extract features. Vote scores are not calibrated probabilities. One dominant animal per image. The user explicitly requires a Windows application and source-code launch with a .bat file; an .exe installer is out of scope. No network use during inference. Preserve trained models and frozen experimental results.

## Evidence on Hand
STL-10 official supervised images, fixed train/validation/test manifests, measured experiments. External photos retain Wikimedia attribution. No benchmark numbers may be invented.

## Product Principles
Keep training and inference consistent. Show the evidence behind retrieval. Use Vietnamese task labels. Keep the evaluation protocol inspectable.
