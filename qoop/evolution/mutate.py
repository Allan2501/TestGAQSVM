import qiskit
import random
from ..backend import utilities, constant
from ..core import random_circuit

def specific_mutate(qc: qiskit.QuantumCircuit, pool, index: int) -> qiskit.QuantumCircuit:
    """Replace a quantum gate at specific index by another

    Args:
        - qc (qiskit.QuantumCircuit): input circuit
        - index (int): from 0 to num_gate - 1

    Returns:
        - qiskit.QuantumCircuit: Bit flipped circut
    """
    while (True):
        new_gate = random.choice(pool)
        if new_gate['num_params'] == 0:
            gate = new_gate['operation']()
        elif new_gate['num_params'] == 1:
            gate = new_gate['operation'](qiskit.circuit.Parameter(f'{index}'))
        else:
            gate = new_gate['operation'](qiskit.circuit.ParameterVector(f'{index}', new_gate['num_params']))
        if gate.num_qubits == qc.data[index].operation.num_qubits:
            break
    target_qubits = qc.data[index][1]
    if gate.num_qubits == 1:
        qc.data[index] = (gate, [target_qubits[0]], [])
    elif gate.num_qubits == 2:
        qc.data[index] = (gate, [target_qubits[0], target_qubits[1]] if len(target_qubits) > 1 else [target_qubits[0]], [])
    return qc

def bitflip_mutate_with_normalizer(pool, normalizer_func, prob_mutate: float = 0.1) -> qiskit.QuantumCircuit:
    """Mutate at every position in circuit with probability = prob_mutate

    Args:
        - qc (qiskit.QuantumCircuit): Input circuit
        - prob_mutate (float, optional): Mutate probability. Defaults to 0.1.

    Returns:
        - qiskit.QuantumCircuit: Bit flipped circuit
    """
    def bitflip_mutate_func(qc: qiskit.QuantumCircuit) -> qiskit.QuantumCircuit:
        num_gates = len(qc.data)
        for index in range(0, num_gates):
            if random.random() < prob_mutate:
                qc = specific_mutate(qc, pool, index = index)  
        return normalizer_func(qc)
    return bitflip_mutate_func


def bitflip_mutate(pool, prob_mutate: float = 0.1) -> qiskit.QuantumCircuit:
    """Mutate at every position in circuit with probability = prob_mutate

    Args:
        - qc (qiskit.QuantumCircuit): Input circuit
        - prob_mutate (float, optional): Mutate probability. Defaults to 0.1.

    Returns:
        - qiskit.QuantumCircuit: Bit flipped circuit
    """
    def bitflip_mutate_func(qc: qiskit.QuantumCircuit) -> qiskit.QuantumCircuit:
        num_gates = len(qc.data)
        for index in range(0, num_gates):
            if random.random() < prob_mutate:
                qc = specific_mutate(qc, pool, index = index)  
        return qc
    return bitflip_mutate_func


def layerflip_mutate(qc: qiskit.QuantumCircuit, prob_mutate: float = 0.1) -> qiskit.QuantumCircuit:
    """Mutate qc to other.

    Args:
        qc (qiskit.QuantumCircuit)
        is_truncate (bool, optional): If it's true, make the qc depth into default. Defaults to True.

    Returns:
        qsee.evolution.eEqc: Mutatant
    """
    standard_depth = qc.depth()
    for index in range(0, standard_depth):
        if random.random() < prob_mutate:
            qc1, qc2 = utilities.divide_circuit_by_depth(qc, index)
            qc21, qc22 = utilities.divide_circuit_by_depth(qc2, 1)
            genome = random_circuit.generate_with_pool(qc.num_qubits, 1)
            qc = utilities.compose_circuit([qc1, genome, qc22])
            qc = utilities.truncate_circuit(qc.copy(), standard_depth)
    return qc
##########################################################################################
#########################################TESTING##########################################
##########################################################################################
def specific_mutate_testing(qc: qiskit.QuantumCircuit, pool, index: int, num_qubits: int) -> qiskit.QuantumCircuit:
    """Replace a quantum gate at specific index by another, ensuring rotational gates match qubits.

    Args:
        - qc (qiskit.QuantumCircuit): input circuit
        - pool (list): available gates pool
        - index (int): gate index to mutate
        - num_qubits (int): number of qubits in the circuit

    Returns:
        - qiskit.QuantumCircuit: Circuit with mutated gate
    """
    # Count current rotational gates
    num_rot_gates = sum(1 for gate in qc.data if gate.operation.name in ["rx", "ry", "rz"])

    # Determine if the current gate at index is rotational
    current_is_rotational = qc.data[index].operation.name in ["rx", "ry", "rz"]

    while True:
        new_gate = random.choice(pool)
        if new_gate['num_params'] == 0:
            gate = new_gate['operation']()
        elif new_gate['num_params'] == 1:
            gate = new_gate['operation'](qiskit.circuit.Parameter(f'{index}'))
        else:
            gate = new_gate['operation'](qiskit.circuit.ParameterVector(f'{index}', new_gate['num_params']))

        # Check compatibility
        if gate.num_qubits == qc.data[index].operation.num_qubits:
            is_rotational = gate.name in ["rx", "ry", "rz"]

            # Ensure we don't reduce the number of rotational gates below the number of qubits
            if is_rotational or (not current_is_rotational and num_rot_gates >= num_qubits):
                break

    # Replace the gate
    target_qubits = qc.data[index][1]
    qc.data[index] = (gate, target_qubits, [])
    return qc

def bitflip_mutate_with_normalizer_testing(pool, normalizer_func, prob_mutate: float = 0.1, num_qubits: int = 4) -> qiskit.QuantumCircuit:
    """Mutate gates in the circuit while normalizing, ensuring rotational gate constraints.

    Args:
        - pool (list): available gates pool
        - normalizer_func (function): normalization function
        - prob_mutate (float): mutation probability
        - num_qubits (int): number of qubits in the circuit

    Returns:
        - function: Mutation function to apply on a circuit
    """
    def bitflip_mutate_func(qc: qiskit.QuantumCircuit) -> qiskit.QuantumCircuit:
        num_gates = len(qc.data)
        for index in range(num_gates):
            if random.random() < prob_mutate:
                qc = specific_mutate_testing(qc, pool, index=index, num_qubits=num_qubits)
        return normalizer_func(qc)

    return bitflip_mutate_func
