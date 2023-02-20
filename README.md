# BaroEconomy
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
The file associations are already in the settings file.

## Tech Stack
- (Javascript Libraries)
  - jQuery
  - Bootstrap
  - Fontawesome5
  - elasticlunr
- Jekyll

# ItemParser
There's a Python file in the working directory thats used to parse out
any data needed from Barotrauma.

## Dependencies

I recommend using a virtual environment.
If you have the Python extension by Microsoft,
you can create an environment from the command palette
and it will automatically activate the env in your default terminal.

If you're on Windows,
you might have to change your default terminal from Powershell to Command Prompt
as scripts are not allowed in Powershell without permissions, which it uses.

Make sure the working directory is NOT '*_working*' when running the python file.

### Python
Python **3.11.x**, nothing less, please update, ya nerd. <br>
Please set up Pylance with basic type checking, if you use VSCode, it comes with the Python extension, turn it on in the bottom right corner.

### OpenCV
`pip install opencv-python` <br>
Gold standard image processing tool,
a bit overkill for this project but very useful and familiar.

### SciPy
`pip install scipy` <br>
Can do some additional analysis, along with numpy.
