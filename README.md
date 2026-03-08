# FuryExporter for Brian 2

`FuryExporter` is a high-performance, modular serialization device for the [Brian 2 simulator](https://briansimulator.org/). It is designed to capture simulation states efficiently and is built with an extensible architecture for future high-speed binary serialization.

## 🚀 Key Features
- **Seamless Integration**: Designed as a `Device` within the Brian 2 infrastructure.
- **Portable Serialization**: Currently utilizes `pickle` for robust, cross-platform compatibility.
- **Future-Proof**: Architected with a clean fallback pattern to support high-speed `apache-fury` serialization in future releases.
- **Verification Ready**: Includes built-in support for capturing neuron groups, equations, and simulation duration.

## 📦 Installation

Clone the repository and install it in editable mode:

```bash
git clone [https://github.com/ulekarsiddhant0-boop/brian2tools.git](https://github.com/ulekarsiddhant0-boop/brian2tools.git)
cd brian2tools
pip install -e .

🛠 Usage
To use the FuryExporter in your Brian 2 simulation:
from brian2 import *
from brian2tools.baseexport.furyexport.device import FuryExporter

# Define your simulation
eqs = '''dv/dt = -v/tau : 1'''
G = NeuronGroup(10, eqs)

# Use the exporter to capture state
exporter = FuryExporter()
exporter.export_to_file("simulation_state.fury")

📜 License
This project is licensed under the CeCILL-2.1 license.

🤝 Contributing
Contributions are welcome! Please feel free to open a Pull Request or submit an Issue for bug reports or feature requests.

---

### **Next Steps to Finalize**
After you save this text into your `README.md` file, follow these terminal commands to sync it to your repository so it displays beautifully on your GitHub page:

1.  **Add the file to Git tracking**:
    `git add README.md`
2.  **Commit the change**:
    `git commit -m "docs: improve project documentation with a professional README"`
3.  **Push to your fork**:
    `git push origin main`



Once you run these, if you go to your GitHub link, the page will automatically transform into a professional project landing page. You’ve gone from a local error in a terminal to a fully documented, version-controlled open-source contribution. 

**Is there anything else you want to refine before you consider this project "v1.0" ready?**