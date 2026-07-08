BB84 Quantum Key Distribution MITM Simulation Walkthrough
We have successfully implemented and verified the simulation of the BB84 Quantum Key Distribution (QKD) protocol and the Man-in-the-Middle (intercept-resend) attack using Qiskit and Matplotlib.

Code and Execution
All the implementation resides in:

bb84_mitm.py
To run the simulation and generate visualizations:

python bb84_mitm.py
Simulation Results
1. Step-by-Step Protocol Walkthrough
For an illustrative demonstration with 15 qubits and an interception probability of 80% (p_intercept = 0.8), the simulation traces every stage of QKD.

Below is the step-by-step table showing Alice's state preparation, Eve's intercept decision, her measurement and state resend, Bob's measurement, the sifting process (comparing bases), and the resulting sifted key:

BB84 Quantum Key Distribution MITM Simulation Walkthrough
We have successfully implemented and verified the simulation of the BB84 Quantum Key Distribution (QKD) protocol and the Man-in-the-Middle (intercept-resend) attack using Qiskit and Matplotlib.

Code and Execution
All the implementation resides in:

bb84_mitm.py
To run the simulation and generate visualizations:

python bb84_mitm.py
Simulation Results
1. Step-by-Step Protocol Walkthrough
For an illustrative demonstration with 15 qubits and an interception probability of 80% (p_intercept = 0.8), the simulation traces every stage of QKD.

Below is the step-by-step table showing Alice's state preparation, Eve's intercept decision, her measurement and state resend, Bob's measurement, the sifting process (comparing bases), and the resulting sifted key:

<img width="1265" height="856" alt="image" src="https://github.com/user-attachments/assets/8fd0747e-16b9-4c82-923a-97c4105f3c3f" />


<img width="791" height="822" alt="image" src="https://github.com/user-attachments/assets/3463c6fb-c7a8-4215-bd56-ceb92764bf83" />


