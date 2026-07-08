import random
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Set non-interactive backend to avoid Tkinter issues
import matplotlib.pyplot as plt
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator

def run_bb84_simulation(num_bits=100, intercept_prob=0.0):
    """
    Simulates the BB84 protocol with a potential Intercept-Resend (MITM) attack.
    
    Parameters:
        num_bits (int): Total number of qubits Alice sends.
        intercept_prob (float): Probability that Eve intercepts a qubit (0.0 to 1.0).
        
    Returns:
        dict: A dictionary containing all arrays and calculated statistics of the run.
    """
    # 1. Alice prepares random bits and bases
    alice_bits = [random.randint(0, 1) for _ in range(num_bits)]
    alice_bases = [random.choice(['Z', 'X']) for _ in range(num_bits)]
    
    # 2. Eve decides which qubits to intercept and her measurement bases
    eve_intercepted = [random.random() < intercept_prob for _ in range(num_bits)]
    eve_bases = [random.choice(['Z', 'X']) if intercepted else None for intercepted in eve_intercepted]
    
    # 3. Bob chooses random measurement bases
    bob_bases = [random.choice(['Z', 'X']) for _ in range(num_bits)]
    
    # 4. Construct Qiskit circuits
    circuits = []
    for i in range(num_bits):
        # 1 qubit, 2 classical bits: c[0] for Bob's measurement, c[1] for Eve's measurement
        qc = QuantumCircuit(1, 2)
        
        # --- Stage 1: Alice Prepares State ---
        if alice_bits[i] == 1:
            qc.x(0)
        if alice_bases[i] == 'X':
            qc.h(0)
            
        # --- Stage 2: Eve Intercepts (intercept-resend) ---
        if eve_intercepted[i]:
            if eve_bases[i] == 'X':
                qc.h(0)
            qc.measure(0, 1)  # Measure qubit 0 to Eve's register c[1]
            if eve_bases[i] == 'X':
                qc.h(0)  # Re-apply H to restore state in diagonal basis
                
        # --- Stage 3: Bob Measures Qubit ---
        if bob_bases[i] == 'X':
            qc.h(0)
        qc.measure(0, 0)  # Measure qubit 0 to Bob's register c[0]
        
        circuits.append(qc)
        
    # 5. Run the circuits
    simulator = AerSimulator()
    job = simulator.run(circuits, shots=1)
    result = job.result()
    
    # Parse measurements
    bob_measured = []
    eve_measured = []
    
    for i in range(num_bits):
        counts = result.get_counts(i)
        # counts is a dict like {'01': 1} or {'11': 1}
        # The bitstring is represented as: 'eve_meas bob_meas' (c[1]c[0])
        bitstring = list(counts.keys())[0]
        # c[0] is at index 1 in a 2-character string
        bob_val = int(bitstring[1])
        bob_measured.append(bob_val)
        
        # If Eve intercepted, read c[1] (index 0 in string)
        if eve_intercepted[i]:
            eve_val = int(bitstring[0])
            eve_measured.append(eve_val)
        else:
            eve_measured.append(None)
            
    # 6. Sifting Phase
    # Alice and Bob compare bases and keep indices where bases matched
    sifted_indices = [i for i in range(num_bits) if alice_bases[i] == bob_bases[i]]
    sifted_len = len(sifted_indices)
    
    alice_sifted_key = [alice_bits[i] for i in sifted_indices]
    bob_sifted_key = [bob_measured[i] for i in sifted_indices]
    
    # 7. Calculate QBER and Info Gain
    # Quantum Bit Error Rate (QBER) is the error rate on sifted keys
    errors = sum(1 for a, b in zip(alice_sifted_key, bob_sifted_key) if a != b)
    qber = (errors / sifted_len) if sifted_len > 0 else 0.0
    
    # Eve's information gain:
    # We define it in two ways:
    # 1. Info Gain: Sifted keys where Eve intercepted AND matched the basis (she knows the key bit with 100% certainty).
    # 2. Key Accuracy: The percentage of the final sifted key that Eve knows (guessing randomly when she didn't intercept or used the wrong basis).
    eve_info_gain_count = 0
    eve_correct_bits = 0
    
    for idx in sifted_indices:
        if eve_intercepted[idx]:
            if eve_bases[idx] == alice_bases[idx]:
                # Eve matched basis, she knows the bit perfectly
                eve_info_gain_count += 1
                eve_correct_bits += 1
            else:
                # Eve got a random outcome because she matched the wrong basis.
                # Does her outcome match Alice's bit?
                if eve_measured[idx] == alice_bits[idx]:
                    eve_correct_bits += 1
        else:
            # Eve didn't intercept, she has to guess (50% average correctness)
            if random.randint(0, 1) == alice_bits[idx]:
                eve_correct_bits += 1
                
    eve_info_gain = (eve_info_gain_count / sifted_len) if sifted_len > 0 else 0.0
    eve_key_accuracy = (eve_correct_bits / sifted_len) if sifted_len > 0 else 0.5
    
    return {
        'alice_bits': alice_bits,
        'alice_bases': alice_bases,
        'eve_intercepted': eve_intercepted,
        'eve_bases': eve_bases,
        'eve_measured': eve_measured,
        'bob_bases': bob_bases,
        'bob_measured': bob_measured,
        'sifted_indices': sifted_indices,
        'alice_sifted_key': alice_sifted_key,
        'bob_sifted_key': bob_sifted_key,
        'qber': qber,
        'eve_info_gain': eve_info_gain,
        'eve_key_accuracy': eve_key_accuracy
    }

def plot_step_by_step(sim_data, num_display=15, save_path="bb84_step_by_step.png"):
    """
    Plots a step-by-step trace of the BB84 protocol for visualization.
    """
    fig, ax = plt.subplots(figsize=(14, 9.5))
    ax.axis('off')
    
    # Title
    ax.text(0.5, 0.98, "BB84 Quantum Key Distribution - Step-by-Step Simulation (MITM Attack)", 
            fontsize=16, fontweight='bold', ha='center', va='top', transform=ax.transAxes)
    
    # We will display the first num_display bits
    n = min(num_display, len(sim_data['alice_bits']))
    
    headers = [
        "Alice's Input Bits",
        "Alice's State Basis",
        "Alice's Prepared State",
        "Eve Intercepted?",
        "Eve's Measurement Basis",
        "Eve's Measured Bit",
        "Bob's Measurement Basis",
        "Bob's Measured Bit",
        "Bases Match (Sifting)?",
        "Alice's Sifted Key",
        "Bob's Sifted Key",
        "Intercept Detectable Error?"
    ]
    
    # Create the grid data
    grid_data = []
    for i in range(n):
        # Prepared state string
        b_alice = sim_data['alice_bits'][i]
        basis_alice = sim_data['alice_bases'][i]
        if basis_alice == 'Z':
            prep_state = "│0⟩" if b_alice == 0 else "│1⟩"
        else:
            prep_state = "│+⟩" if b_alice == 0 else "│-⟩"
            
        intercepted = "Yes" if sim_data['eve_intercepted'][i] else "No"
        eve_basis = sim_data['eve_bases'][i] if sim_data['eve_intercepted'][i] else "-"
        eve_meas = str(sim_data['eve_measured'][i]) if sim_data['eve_intercepted'][i] else "-"
        
        bob_basis = sim_data['bob_bases'][i]
        bob_meas = sim_data['bob_measured'][i]
        
        bases_match = basis_alice == bob_basis
        sifting = "Yes ✔" if bases_match else "No"
        
        alice_sifted = str(b_alice) if bases_match else "-"
        bob_sifted = str(bob_meas) if bases_match else "-"
        
        detected = "-"
        if bases_match:
            detected = "No" if b_alice == bob_meas else "YES ✘"
            
        grid_data.append([
            str(b_alice),
            basis_alice,
            prep_state,
            intercepted,
            eve_basis,
            eve_meas,
            bob_basis,
            str(bob_meas),
            sifting,
            alice_sifted,
            bob_sifted,
            detected
        ])
        
    # Draw table
    col_width = 1.0 / (len(headers) + 1)
    row_height = 0.028
    
    # Header styling
    for col_idx, header in enumerate(headers):
        x = 0.05 + col_idx * 0.078
        y = 0.81
        ax.text(x + 0.035, y, header, fontsize=9, fontweight='bold', ha='center', va='center', rotation=45)
        
    # Table data
    for row_idx in range(n):
        y = 0.74 - (row_idx * row_height)
        
        # Alternating row colors
        rect = plt.Rectangle((0.02, y - row_height/2), 0.96, row_height, 
                             facecolor='#f0f4f8' if row_idx % 2 == 0 else '#ffffff', 
                             edgecolor='none', zorder=-1)
        ax.add_patch(rect)
        
        # Row index label
        ax.text(0.03, y, f"Qubit {row_idx}", fontsize=9, fontweight='normal', ha='left', va='center')
        
        # Row values
        for col_idx, val in enumerate(grid_data[row_idx]):
            x = 0.05 + col_idx * 0.078
            
            # Formatting highlight for error or match
            fg_color = 'black'
            weight = 'normal'
            if col_idx == 8 and "Yes" in val:
                fg_color = 'green'
                weight = 'bold'
            elif col_idx == 11 and "YES ✘" in val:
                fg_color = 'red'
                weight = 'bold'
                
            ax.text(x + 0.035, y, val, fontsize=10, ha='center', va='center', color=fg_color, fontweight=weight)
            
    # Summary info boxes
    sifted_indices = sim_data['sifted_indices']
    qber = sim_data['qber']
    eve_gain = sim_data['eve_info_gain']
    
    info_text = (
        f"Simulation Summary (First {n} Qubits Displayed):\n"
        f"🔹 Total Sent Qubits: {len(sim_data['alice_bits'])}\n"
        f"🔹 Sifted key length: {len(sifted_indices)} bits\n"
        f"🔹 Quantum Bit Error Rate (QBER): {qber:.2%} "
        f"({'Intrusion Detected!' if qber > 0.11 else 'Likely Secure (QBER < 11%)'})\n"
        f"🔹 Eve's Info Leaked (sifted key in matching basis): {eve_gain:.2%}\n"
        f"🔹 Eve's Sifted Key Correctness: {sim_data['eve_key_accuracy']:.2%}"
    )
    
    ax.text(0.05, 0.08, info_text, fontsize=11, fontweight='bold', bbox=dict(boxstyle="round", facecolor='#fff9db', edgecolor='#ffe066'))
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=300)
    plt.close()
    print(f"Detailed step-by-step figure saved to '{save_path}'")
# (plot_parameter_sweep was removed to simplify the codebase)

def plot_security_bar_chart(save_path="bb84_security_bar_chart.png", num_runs=15, bits_per_run=200):
    """
    Plots a simplified bar chart comparing the Quantum Bit Error Rate (QBER) 
    against the 11% security threshold for distinct eavesdropping scenarios.
    """
    scenarios = {
        "No Attack\n(p=0.0)": 0.0,
        "Low Attack\n(p=0.2)": 0.2,
        "Medium Attack\n(p=0.5)": 0.5,
        "Full MITM Attack\n(p=1.0)": 1.0
    }
    
    label_list = list(scenarios.keys())
    qber_means = []
    
    for label, p in scenarios.items():
        qbers = []
        for _ in range(num_runs):
            data = run_bb84_simulation(num_bits=bits_per_run, intercept_prob=p)
            qbers.append(data['qber'])
        qber_means.append(np.mean(qbers))
        
    fig, ax = plt.subplots(figsize=(8, 6))
    
    # 11% threshold line
    threshold = 0.11
    plt.axhline(y=threshold, color='#e03131', linestyle='--', linewidth=2, label="Security Threshold (11% QBER)")
    
    # Define colors based on whether QBER exceeds threshold
    colors = ['#2b8a3e' if q < threshold else '#c92a2a' for q in qber_means]
    
    # Create bar chart
    bars = plt.bar(label_list, qber_means, color=colors, edgecolor='#333333', width=0.5)
    
    # Annotate bar values
    for bar in bars:
        height = bar.get_height()
        ax.annotate(f'{height:.2%}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),  # 3 points vertical offset
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=10, fontweight='bold')
        
    # Formatting
    plt.title("Simplified Security Analysis: QBER vs. Safety abort threshold", fontsize=13, fontweight='bold', pad=15)
    plt.ylabel("Quantum Bit Error Rate (QBER)", fontsize=11)
    plt.ylim(-0.02, 0.32)
    plt.grid(axis='y', linestyle=':', alpha=0.5)
    
    # Add colored status boxes near the bottom
    info_box = (
        "Status Legend:\n"
        "🟢 Green Bar: QBER < 11% (Secure — proceed with Key derivation)\n"
        "🔴 Red Bar: QBER >= 11% (Aborted — Eavesdropping detected)"
    )
    fig.text(0.12, 0.02, info_box, fontsize=9.5, bbox=dict(boxstyle="round,pad=0.4", facecolor='#f8f9fa', edgecolor='#dee2e6'))
    
    plt.legend(loc='upper left', fontsize=10)
    plt.tight_layout(rect=[0, 0.14, 1, 1])
    plt.savefig(save_path, dpi=300)
    plt.close()
    print(f"Security bar chart saved to '{save_path}'")

if __name__ == "__main__":
    print("=" * 60)
    print("Starting BB84 QKD Protocol Simulation with Intercept-Resend Attack")
    print("=" * 60)
    
    # 1. Run a detailed step-by-step example with Eve intercepting with 80% probability
    # representing a strong attack
    print("\nRunning single illustrative demonstration (N=15, p_intercept=0.8)...")
    demo_data = run_bb84_simulation(num_bits=15, intercept_prob=0.8)
    
    print("\n[Step-by-Step Overview]")
    print(f"Alice's bits:  {demo_data['alice_bits']}")
    print(f"Alice's bases: {demo_data['alice_bases']}")
    print(f"Bob's bases:   {demo_data['bob_bases']}")
    print(f"Bob's measured:{demo_data['bob_measured']}")
    print(f"Sifted indices:{demo_data['sifted_indices']}")
    print(f"Alice's key:   {demo_data['alice_sifted_key']}")
    print(f"Bob's key:     {demo_data['bob_sifted_key']}")
    print(f"QBER:          {demo_data['qber']:.2%}")
    print(f"Eve's Info:    {demo_data['eve_info_gain']:.2%}")
    
    # Save the step-by-step detailed table visualization
    plot_step_by_step(demo_data, num_display=15, save_path="bb84_step_by_step.png")
    
    # (Parameter sweep removed per user configuration)
    
    # 3. Run simplified bar chart simulation
    print("\nRunning simplified security bar chart simulation...")
    plot_security_bar_chart(save_path="bb84_security_bar_chart.png", num_runs=15, bits_per_run=150)
    
    print("\nSimulation complete. Please check the generated png files.")
    print("=" * 60)
