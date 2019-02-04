# Introduction

According to the official FIDE Regulations a game of chess - in some special cases - could end in a draw either by the claim of the player or the intervention of the arbiter.
These cases are:

* 3 Fold Repetition(claim by player)
* 50 Moves Rule (claim by player)
* 5 Fold Repetition (arbiter should intervene)
* 75 Moves Rule (arbiter should intervene)

*Detailed explanation: [FIDE Laws of Chess - Article 9](http://www.fide.com/fide/handbook.html?id=208&view=article)*

The idea behind this program is to perform checks <b> in a real time updating pgn</b> for these claims and help the arbiter intervene accordingly.

This will be especially useful for tournaments where the games are recorded with the [DGT Livechess software](http://www.digitalgametechnology.com/index.php/products/electronic-boards/serial-tournament/285-dgt-livechess-software13?mavikthumbnails_display_ratio=2) (or any other similar software).

The program is meant to work using either local pgn files and/or pgn files from the web. This means that is an independent, from the live games operator, tool and can be used like football VAR by the arbiters.

# Operating System

This version is compatible with the macOS and Windows.


# Dependencies
* Python 3
* PyQt 5  
```
pip install pyqt5
```
* [python-chess ](https://github.com/niklasf/python-chess)by Niklas Fiekas  
```
pip install python-chess
```

# Usage
The program should start by running the main.py
```
$ python main.py
```  

## Screenshots
Here is how the GUI looks like (on macOS) while the program is running:

<img src="./screenshots/action.png" width="50%"/>





