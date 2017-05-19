# ASP-Graph

ASP-Graph is a diagramatic tool for logic programming within the Answer Set Programming paradigm (ASP). Its aim is to provide a diagrammatic alternative to the traditional symbolic reasoning used when creating logic programs. It is based on a diagrammatic reasoning system known as "Existential Graphs", introduced by Charles S. Peirce in the late 20th century.

Uses the [Potsdam Answer Set Solving Collection](https://potassco.org/) as back-end. GUI made with [Kivy library](https://kivy.org).

At the moment, ASP-Graph runs only on GNU/Linux.

## Usage

The interface has three main parts:

	- Main Menu Bar: Traditional menu bar with all available functions.
	- Canvas: The place to draw diagrams.
	- Side Panel: Used for managing names and predicate properties.

The canvas has two operating modes: SELECT and INSERT. Graph creation is done entirely with the mouse. The keyboard is only used for shortcuts.

| Mode    | Left-Click | Right-Click | Middle Button | Scroll |
|:-------:|:----------:|:-----------:|:-------------:|:------:|
| INSERT  | Add item   | Delete item | Pan           | Zoom   |
| SELECT  | Move item  | Resize item | Pan           | Zoom   |

## Shortcuts

| Key     | Action           |
|---------|-----------------:|
| E       | INSERT Mode      |
| S       | SELECT Mode      |
| 1       | Literal          |
| 2       | Ellipse          |
| 3       | Rectangle        |
| T       | Toggle Panel     |
| TAB     | Focus name input |
| Q       | Quit             |
