
# Dialogue Maker

## Instalation

### 1. Install Dependencies
```
pip install -r requirements.txt
```

### 2. Run the Application
```
python Main.py
```

## Features

- Visual node-based editor for dialogue graphs
- Create, edit, and delete dialogue nodes
- Global variable management panel
- Connect nodes with execution and data sockets
- Context menu for adding nodes and reroute points
- Properties panel for editing node details
- Inspired by Unreal Engine Blueprints

## Folder Structure

```
.
├── Core/
│   ├── BaseNode.py
│   ├── VariableManager.py
│   ├── Graph/
│   │   ├── SocketItem.py
│   │   └── EdgeItem.py
│   ├── Nodes/
│   │   ├── StartNode.py
│   │   ├── DialogueNode.py
│   │   └── SetVarNode.py
│   └── View/
│       ├── GraphScene.py
│       └── GraphView.py
├── Style.py
├── Main.py
└── requirements.txt
```

## Usage

- Right-click on the canvas to add nodes
- Drag from sockets to connect nodes
- Double-click edges to insert reroute nodes
- Use the left panel to manage global variables
- Use the right panel to edit node properties
- Save, load, and export your dialogue graphs from the File menu

## License

Private project only
