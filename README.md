
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
│   ├── Enums/
│   │   └── DataType.py
│   ├── Graph/
│   │   ├── EdgeItem.py
│   │   └── SocketItem.py
│   ├── Nodes/
│   │   ├── DialogueNode.py
│   │   ├── RerouteNode.py
│   │   ├── SetVarNode.py
│   │   └── StartNode.py
│   ├── Structures/
│   │   └── Property.py
│   ├── UIPanel/
│   │   ├── Utils/
│   │   │   ├── PropertyWidgetFactory.py
│   │   │   └── TypeDelegate.py
│   │   ├── GlobalVariablePanel.py
│   │   └── PropertiesPanel.py
│   ├── View/
│   │   ├── GraphScene.py
│   │   └── GraphView.py
│   ├── BaseNode.py
│   ├── UIPanelBase.py
│   └── VariableManager.py
├── .gitignore
├── Cleanup.py
├── Main.py
├── README.md
├── requirements.txt
└── Style.py
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
