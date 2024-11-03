# StorageTrauma
Manager and calculator for your submarines inventory with the game economy in the game Barotrauma.

This program is a webapp, statically generated through GitHub. <br>
All calculations are done through local javascript.

## Local Deployment
Use `jekyll serve --open-url --baseurl=''` to build and serve the website.
It will automatically update and changes to file except the config file.
I added a VSCode task to the tasks file for you.

The `_config.yml` file is used by Jekyll, changes to it will not automatically
update the website, you will need to re-serve the site.

## Dependencies
### Jekyll
Used to statically generate the site, GitHub uses it.
You can view the [website here](https://jekyllrb.com/).
You need RubyGems to install it.

### Liquid
Jekyll uses Liquid, a templating engine. <br>
While not needed, having intellisense support for it is **very** helpful.

If you're using VSCode, you can get the Liquid extension: `sissel.shopify-liquid`. <br>
The file associations are already in the settings file. <br>
I tend to use the HTML/Javascript intellisense as much as possible as it is better, but switch to Liquid when needed.

## Tech Stack
- (Javascript Libraries)
  - jQuery
  - Bootstrap
  - datatables
  - Feather
  - Fontawesome5
  - elasticlunr
- Jekyll

# ItemParser
There's a Python file in the working directory thats used to parse out
any data needed from Barotrauma.

## ItemParser.py
The main file, contains a bunch of functions for reading or writing from or to certain files. <br>
It imports from the other files and you can comment out/in certain lines within main to do certain things.

## ToJson.py
Contains a single function `to_json` and a bunch of assisting dispatch functions. <br>
Should hopefully be able to convert any object to valid json text, can always add a new function when needed.

## ItemImageDownloader.py
Contains a single class for downloading and parsing out the icons or sprites from the sprite sheets. <br>
Uses OpenCV and numpy to do its parsing, so you'll either need those or you can just ignore it by commenting out the import&usage lines from `ItemParser.main()`.

## BaroInterface.py
Contains a bunch of classes that act as interfaces for the Barotrauma items. <br>
The game stores all item data as XML, these classes should all contains a `from_Element` class method to construct them from an XML Element. <br>
They should also all have support within the `to_json` dispatch function.

## Dependencies

I recommend using a virtual environment.
If you have the Python extension by Microsoft,
you can create an environment from the command palette
and it will automatically activate the env in your default terminal.

If you're on Windows,
you might have to change your default terminal from Powershell to Command Prompt
as scripts are not allowed in Powershell without permissions, which it uses.

Make sure the working directory is NOT '*_working*' when running the python file. Except when running tests.

### Python
Python **3.11.x** or higher, nothing less, please update, ya nerd. <br>
Please set up Pylance with basic type checking, if you use VSCode, it comes with the Python extension, turn it on in the bottom right corner.

### OpenCV
`pip install opencv-python` <br>
Gold standard image processing tool,
a bit overkill for this project but very useful and familiar.

### SciPy
`pip install scipy` <br>
Can do some additional analysis, along with numpy.
