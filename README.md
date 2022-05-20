# API Consumer
## Description
API Consumer is a part of DS4A/Data Engineering - Project Team 18's group project. It is a program that can efficiently consume any API as long as the API's crucial metadata has been recorded into the program's memory stores and its calling pattern falls within the program's growing heuristics. Received payloads are saved as CSV's (in the project's **output** subdirectory) where they can be analyzed and/or utilized downstream. API Consumer self-regulates every time you run it. As a result, any data retrieved from an endpoint will be new data from the last time you ran API Consumer for that specific endpoint.

## Getting Started

### Installation

1. [Install Python 3 (at least v3.7.8 or later)](https://python.land/installing-python) on your system, if you don't have it.

*Optional: Alternatively, you can install and use pyenv instead. [Pyenv](https://github.com/pyenv/pyenv) is a command line tool that allows you to install, uninstall, and switch seaminglessly between multiple versions of Python. [Click here](https://github.com/pyenv/pyenv#Installation) for instructions on how to install and use pyenv.* 


2. [Clone this repository](https://docs.github.com/en/repositories/creating-and-managing-repositories/cloning-a-repository) into a local directory of your choice and keep a note of the fully qualified path.

### Dependencies
*Optional: It is not necessary but highly recommended that you initialize and utilize a virtual environment before installing dependencies for any Python project. Please [click here](https://realpython.com/python-virtual-environments-a-primer/) to learn more about why you would want to use virtual environments, how to set them up, how to use them, etc.*

To install the program's dependencies, you just need to pip install the dependencies listed in the project's *requirements.txt*. You can do so by copying the following command, replace the bolded text with the noted fully qualifed path from Installation - Step 2, and then executing the modified command in a command session:

<code>pip install -r **(replace all this bolded text with the fully qualified path from Installation - Step 2)**/requirements.txt</code>

### Configurations

Some API's require authentication before they can be consumed. Authentication methods can vary significantly between API's. Consqeuently, you must refer to the respective source in order to obtain the appropriate means of access.

Once proper access has been attained, API Consumer expects authentication data to be stored and retrieved in  *credentials.ini*. You must manually create *credentials.ini* (to be located in the **configs** subdirectory) for obvious security reasons. However, there is no need to figure out how to fill out this configuration file from scratch. Please refer to *credentials_template.ini* (also located in the **configs** subdirectory) as your guiding light. You can copy and paste the content into *credentials.ini* and then fill it out accordingly.

The structure of *credentials.ini* is as follows:
<img src="/assets/Credentials.png" width="720" height="405"/>

Every section maps to a source code/alias. Key-value pairs that exist within a section stores a particular value required for source authentication. It should be noted that storing sensitive data in this manner is not ideal but will suffice given the nature of the project.

Currently, API Consumer supports only plain unsecured authentications. However, as the project progresses and encounters more authentications; so too will the program's capabilities once the new authentication method patterns are implemented and added to the memory stores.

**That's it! API Consumer is set up and ready for consumption.**

## Usage

API Consumer has three modes of operation - Canned, Semi-Canned, and Manual Mode. API Consumer must be in one of the modes in order to operate. The activation of a mode is controlled by a specific combination of command line arguments. There are three command line options which the program recognizes: 

**source** - A code/alias that indicates the API that is to be consumed. Please refer to *core.ini* (located in the project's **configs** subdirectory) for more information.

**states** - A comma-separated string of states you want to process during runtime (states must be declared in their abbreviated form).

**manual** - A switch which activates manual mode.

The combination you supply will determine the mode which is active during program runtime. So, to run API Consumer, you need to execute the *api_consumer.py* module (located in the project's **code** subdirectory) along with passing one of the following command line argument combinations: 

### Canned Mode
Canned mode will consume all states for a particular given source.
```
python api_consumer.py --source=fema_e_1
```
<img src="/assets/Canned.gif" width="720" height="405"/>

### Semi-Canned Mode
Semi-Canned Mode will consume a defined set of states you provide for a particular given source.
```
python api_consumer.py --source=fema_e_1 --states=ND,NC,TX,CA
```
<img src="/assets/Semi-Canned.gif" width="720" height="405"/>

### Manual Mode
Manual Mode will prompt you to enter the query string you wish to incorporate into the API call of a particular given source. 
```
python api_consumer.py --source=fema_e_1 --manual
```
<img src="/assets/Manual.gif" width="720" height="405"/>

## Version History
* 1.0
    * Initial release