# ChiX - Professional VS Code-inspired C Code Editor

![ChiX Editor](generated-icon.png)

ChiX is a professional-grade C code editor inspired by Visual Studio Code, designed to provide a modern, feature-rich development environment for C programming.

## Features

- **Modern UI/UX**: Clean, professional interface with intuitive controls
- **Syntax Highlighting**: Advanced syntax highlighting for C code
- **Line Numbers**: Clear line numbering with current line highlight
- **Code Suggestions**: Intelligent code completion and suggestions
- **Multi-File Editing**: Tabbed interface for working with multiple files
- **Integrated Compiler**: Compile and run C code directly from the editor
- **Theming Support**: Light and dark themes with customizable colors
- **Project Management**: Organize and manage your C projects efficiently

## Installation

### Windows

Download the latest release from the [Releases](https://github.com/PrakharDoneria/ChiX/releases) page and run the executable.

### From Source

```bash
# Clone the repository
git clone https://github.com/PrakharDoneria/ChiX.git
cd ChiX

# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

## Requirements

- Python 3.10+
- Dependencies:
  - customtkinter
  - pygments
  - keyboard
  - ttkbootstrap
  - pillow

## Building from Source

To build the executable yourself:

```bash
pip install pyinstaller
pyinstaller main.py --onefile --noconsole --name ChiX --icon=generated-icon.png
```

The executable will be available in the `dist` directory.

## Usage

1. Launch the application
2. Create a new file or open an existing one
3. Write your C code with syntax highlighting and code suggestions
4. Compile and run your code using the built-in tools
5. Use keyboard shortcuts for common operations

## Keyboard Shortcuts

- `Ctrl+N`: New file
- `Ctrl+O`: Open file
- `Ctrl+S`: Save file
- `Ctrl+Shift+S`: Save file as
- `Ctrl+Tab`: Switch between tabs
- `F5`: Compile and run code
- `F9`: Toggle theme (Light/Dark)
- `Ctrl+F`: Find in file
- `Ctrl+H`: Replace in file

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- Created by Prakhar Doneria
- Inspired by Visual Studio Code's interface and functionality
- Built with Python and CustomTkinter