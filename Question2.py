from __future__ import print_function
import os
import copy

# Function List:
# 1. netRead: read the benchmark file and build circuit netlist
# 2. faultGate: function that will work on the logic of each gate and also for fault wires
# 3. inputRead: function that will update the circuit dictionary made in netRead to hold the line values
# 4. basic_sim: the actual simulation
# 5. main: The main function
# -------------------------------------------------------------------------------------------------------------------- #
# FUNCTION: Neatly prints the Circuit Dictionary:
def printCkt(circuit):
    print("INPUT LIST:")
    for x in circuit["INPUTS"][1]:
        print(x + "= ", end='')
        print(circuit[x])

    print("\nOUTPUT LIST:")
    for x in circuit["OUTPUTS"][1]:
        print(x + "= ", end='')
        print(circuit[x])

    print("\nGATE list:")
    for x in circuit["GATES"][1]:
        print(x + "= ", end='')
        print(circuit[x])
    print()


# -------------------------------------------------------------------------------------------------------------------- #
# FUNCTION: Reading in the Circuit gate-level netlist file:
def netRead(netName):
    # Opening the netlist file:
    netFile = open(netName, "r")

    # temporary variables
    inputs = []  # array of the input wires
    outputs = []  # array of the output wires
    gates = []  # array of the gate list
    inputBits = 0  # the number of inputs needed in this given circuit


    # main variable to hold the circuit netlist, this is a dictionary in Python, where:
    # key = wire name; value = a list of attributes of the wire
    circuit = {}

    # Reading in the netlist file line by line
    for line in netFile:

        # NOT Reading any empty lines
        if (line == "\n"):
            continue

        # Removing spaces and newlines
        line = line.replace(" ", "")
        line = line.replace("\n", "")

        # NOT Reading any comments
        if (line[0] == "#"):
            continue

        # @ Here it should just be in one of these formats:
        # INPUT(x)
        # OUTPUT(y)
        # z=LOGIC(a,b,c,...)

        # Read a INPUT wire and add to circuit:
        if (line[0:5] == "INPUT"):
            # Removing everything but the line variable name
            line = line.replace("INPUT", "")
            line = line.replace("(", "")
            line = line.replace(")", "")

            # Format the variable name to wire_*VAR_NAME*
            line = "wire_" + line

            # Error detection: line being made already exists
            if line in circuit:
                msg = "NETLIST ERROR: INPUT LINE \"" + line + "\" ALREADY EXISTS PREVIOUSLY IN NETLIST"
                print(msg + "\n")
                return msg

            # Appending to the inputs array and update the inputBits
            inputs.append(line)

            # add this wire as an entry to the circuit dictionary
            circuit[line] = ["INPUT", line, False, 'U']

            inputBits += 1
            print(line)
            print(circuit[line])
            continue

        # Read an OUTPUT wire and add to the output array list
        # Note that the same wire should also appear somewhere else as a GATE output
        if line[0:6] == "OUTPUT":
            # Removing everything but the numbers
            line = line.replace("OUTPUT", "")
            line = line.replace("(", "")
            line = line.replace(")", "")

            # Appending to the output array
            outputs.append("wire_" + line)
            continue

        # Read a gate output wire, and add to the circuit dictionary
        lineSpliced = line.split("=")  # splicing the line at the equals sign to get the gate output wire
        gateOut = "wire_" + lineSpliced[0]

        # Error detection: line being made already exists
        if gateOut in circuit:
            msg = "NETLIST ERROR: GATE OUTPUT LINE \"" + gateOut + "\" ALREADY EXISTS PREVIOUSLY IN NETLIST"
            print(msg + "\n")
            return msg

        # Appending the dest name to the gate list
        gates.append(gateOut)

        lineSpliced = lineSpliced[1].split("(")  # splicing the line again at the "("  to get the gate logic
        logic = lineSpliced[0].upper()


        lineSpliced[1] = lineSpliced[1].replace(")", "")
        terms = lineSpliced[1].split(",")  # Splicing the the line again at each comma to the get the gate terminals
        # Turning each term into an integer before putting it into the circuit dictionary
        terms = ["wire_" + x for x in terms]

        # add the gate output wire to the circuit dictionary with the dest as the key
        circuit[gateOut] = [logic, terms, False, 'U']
        print(gateOut)
        print(circuit[gateOut])

    # now after each wire is built into the circuit dictionary,
    # add a few more non-wire items: input width, input array, output array, gate list
    # for convenience

    circuit["INPUT_WIDTH"] = ["input width:", inputBits]
    circuit["INPUTS"] = ["Input list", inputs]
    circuit["OUTPUTS"] = ["Output list", outputs]
    circuit["GATES"] = ["Gate list", gates]

    print("\n bookkeeping items in circuit: \n")
    print(circuit["INPUT_WIDTH"])
    print(circuit["INPUTS"])
    print(circuit["OUTPUTS"])
    print(circuit["GATES"])


    return circuit


# -------------------------------------------------------------------------------------------------------------------- #
# FUNCTION: calculates the output value for each logic gate
def faultGate(circuit, node, linespliced):

    terminals = list(circuit[node][1])
    accessed = False

    print ("THE FAULT IN CONSIDERATION")
    print (linespliced)

    # get fault node, terminal, and value
    if(linespliced!={}):
        if (linespliced[1] == 'IN'):
            fault_wire_node = 'wire_' + linespliced[0]
            fault_wire_term = 'wire_' + linespliced[2]
            fault_wire_val = linespliced[4]
            # print (fault_wire_node)
            # print (fault_wire_term)
            # print (fault_wire_val)
        else:
            fault_wire_term = 'wire_' + linespliced[0]
            fault_wire_node = fault_wire_term
            fault_wire_val = linespliced[2]
            # print (fault_wire_node)
            # print (fault_wire_term)



        old_val = circuit[fault_wire_term][3]
        # print(old_val)

        # Change gate input terminal wire value to stuck-at value
        if node == fault_wire_node and linespliced[1] == 'IN':
            for term in terminals:
                if (term == fault_wire_term):
                    circuit[term][3] = fault_wire_val
                    accessed = True
                    # print(term + " is ")
                    # print(circuit[term][3])
        # Change wire value to stuck-at value
        elif linespliced[1] != 'IN':
            for term in terminals:
                if (term == fault_wire_term):
                    accessed = True
                    circuit[fault_wire_term][3] = fault_wire_val
                    # print(fault_wire_term + " now has ")
                    # print(circuit[fault_wire_term][3])
    else:

        old_val=""
    # If the node is an Inverter gate output, solve and return the output
    if circuit[node][0] == "NOT":
        if circuit[terminals[0]][3] == '0':
            circuit[node][3] = '1'
        elif circuit[terminals[0]][3] == '1':
            circuit[node][3] = '0'
        elif circuit[terminals[0]][3] == "U":
            circuit[node][3] = "U"
        else:  # Should not be able to come here
            return -1
        if accessed:
            # restore to original value before stuck-at so that it will disrupt other processes that use same wire
            circuit[fault_wire_term][3] = old_val
        return circuit

    # If the node is an AND gate output, solve and return the output
    elif circuit[node][0] == "AND":
        # Initialize the output to 1
        circuit[node][3] = '1'
        # Initialize also a flag that detects a U to false
        unknownTerm = False  # This will become True if at least one unknown terminal is found

        # if there is a 0 at any input terminal, AND output is 0. If there is an unknown terminal, mark the flag
        # Otherwise, keep it at 1
        for term in terminals:
            if circuit[term][3] == '0':
                circuit[node][3] = '0'
                break
            if circuit[term][3] == "U":
                unknownTerm = True
            if accessed:

                circuit[fault_wire_term][3] = old_val
        if unknownTerm:
            if circuit[node][3] == '1':
                circuit[node][3] = "U"
        if accessed:
            # restore to original value before stuck-at so that it will disrupt other processes that use same wire
            circuit[fault_wire_term][3] = old_val
        return circuit

    # If the node is a NAND gate output, solve and return the output
    elif circuit[node][0] == "NAND":
        # Initialize the output to 0
        circuit[node][3] = '0'
        # Initialize also a variable that detects a U to false
        unknownTerm = False  # This will become True if at least one unknown terminal is found

        # if there is a 0 terminal, NAND changes the output to 1. If there is an unknown terminal, it
        # changes to "U" Otherwise, keep it at 0
        for term in terminals:
            if circuit[term][3] == '0':
                circuit[node][3] = '1'
                break
            if circuit[term][3] == "U":
                unknownTerm = True
                break

        if unknownTerm:
            if circuit[node][3] == '0':
                circuit[node][3] = "U"
        if accessed:

            circuit[fault_wire_term][3] = old_val
        return circuit

    # If the node is an OR gate output, solve and return the output
    elif circuit[node][0] == "OR":
        # Initialize the output to 0
        circuit[node][3] = '0'
        # Initialize also a variable that detects a U to false
        unknownTerm = False  # This will become True if at least one unknown terminal is found

        # if there is a 1 terminal, OR changes the output to 1. Otherwise, keep it at 0
        for term in terminals:
            if circuit[term][3] == '1':
                circuit[node][3] = '1'
                break
            if circuit[term][3] == "U":
                unknownTerm = True

        if unknownTerm:
            if circuit[node][3] == '0':
                circuit[node][3] = "U"
        if accessed:
            # restore to original value before stuck-at so that it will disrupt other processes that use same wire
            circuit[fault_wire_term][3] = old_val
        return circuit

    # If the node is an NOR gate output, solve and return the output
    if circuit[node][0] == "NOR":
        # Initialize the output to 1
        circuit[node][3] = '1'
        # Initialize also a variable that detects a U to false
        unknownTerm = False  # This will become True if at least one unknown terminal is found

        # if there is a 1 terminal, NOR changes the output to 0. Otherwise, keep it at 1
        for term in terminals:
            if circuit[term][3] == '1':
                circuit[node][3] = '0'
                break
            if circuit[term][3] == "U":
                unknownTerm = True
        if unknownTerm:
            if circuit[node][3] == '1':
                circuit[node][3] = "U"
        if accessed:
            # restore to original value before stuck-at so that it will disrupt other processes that use same wire
            circuit[fault_wire_term][3] = old_val
        return circuit

    # If the node is an XOR gate output, solve and return the output
    if circuit[node][0] == "XOR":
        # Initialize a variable to zero, to count how many 1's in the terms
        count = 0

        # if there are an odd number of terminals, XOR outputs 1. Otherwise, it should output 0
        for term in terminals:
            if circuit[term][3] == '1':
                count += 1  # For each 1 bit, add one count
            if circuit[term][3] == "U":
                circuit[node][3] = "U"
                if accessed:
                    # restore to original value before stuck-at so that it will disrupt other processes that use same wire
                    circuit[fault_wire_term][3] = old_val
                return circuit

        # check how many 1's we counted
        if count % 2 == 1:  # if more than one 1, we know it's going to be 0.
            circuit[node][3] = '1'
        else:  # Otherwise, the output is equal to how many 1's there are
            circuit[node][3] = '0'
        if accessed:
            # restore to original value before stuck-at so that it will disrupt other processes that use same wire
            circuit[fault_wire_term][3] = old_val
        return circuit

    # If the node is an XNOR gate output, solve and return the output
    elif circuit[node][0] == "XNOR":
        # Initialize a variable to zero, to count how many 1's in the terms
        count = 0

        # if there is a single 1 terminal, XNOR outputs 0. Otherwise, it outputs 1
        for term in terminals:
            if circuit[term][3] == '1':
                count += 1  # For each 1 bit, add one count
            if circuit[term][3] == "U":
                circuit[node][3] = "U"
                if accessed:
                    # restore to original value before stuck-at so that it will disrupt other processes that use same wire
                    circuit[fault_wire_term][3] = old_val
                return circuit

        # check how many 1's we counted
        if count % 2 == 1:  # if more than one 1, we know it's going to be 0.
            circuit[node][3] = '1'
        else:  # Otherwise, the output is equal to how many 1's there are
            circuit[node][3] = '0'
        if accessed:
            # restore to original value before stuck-at so that it will disrupt other processes that use same wire
            circuit[fault_wire_term][3] = old_val
        return circuit

    # Error detection... should not be able to get at this point
    return circuit[node][0]

# -------------------------------------------------------------------------------------------------------------------- #
# FUNCTION: Updating the circuit dictionary with the input line, and also resetting the gates and output lines
def inputRead(circuit, line):
    # Checking if input bits are enough for the circuit
    if len(line) < circuit["INPUT_WIDTH"][1]:
        return -1

    # Getting the proper number of bits:
    line = line[(len(line) - circuit["INPUT_WIDTH"][1]):(len(line))]

    # Adding the inputs to the dictionary
    # Since the for loop will start at the most significant bit, we start at input width N
    i = circuit["INPUT_WIDTH"][1] - 1
    inputs = list(circuit["INPUTS"][1])
    # dictionary item: [(bool) If accessed, (int) the value of each line, (int) layer number, (str) origin of U value]
    for bitVal in line:
        bitVal = bitVal.upper()  # in the case user input lower-case u
        circuit[inputs[i]][3] = bitVal  # put the bit value as the line value
        circuit[inputs[i]][2] = True  # and make it so that this line is accessed

        # In case the input has an invalid character (i.e. not "0", "1" or "U"), return an error flag
        if bitVal != "0" and bitVal != "1" and bitVal != "U":
            return -2
        i -= 1  # continuing the increments

    return circuit

# -------------------------------------------------------------------------------------------------------------------- #
# FUNCTION: the actual simulation #
def basic_sim(circuit,linespliced={}):
    # QUEUE and DEQUEUE
    # Creating a queue, using a list, containing all of the gates in the circuit
    queue = list(circuit["GATES"][1])
    i = 1

    while True:

        i -= 1
        # If there's no more things in queue, done
        if len(queue) == 0:
            break

        # Remove the first element of the queue and assign it to a variable for us to use
        curr = queue[0]
        queue.remove(curr)

        # initialize a flag, used to check if every terminal has been accessed
        term_has_value = True

        # Check if the terminals have been accessed
        for term in circuit[curr][1]:
            if not circuit[term][2]:
                term_has_value = False
                break

        if term_has_value:
            if(circuit[curr][2] == False):
                circuit = faultGate(circuit, curr,linespliced)

            circuit[curr][2] = True

            # ERROR Detection if LOGIC does not exist
            if isinstance(circuit, str):
                print(circuit)
                return circuit

            print("Progress: updating " + curr + " = " + circuit[curr][3] + " as the output of " + circuit[curr][0] + " for:")
            for term in circuit[curr][1]:
                print(term + " = " + circuit[term][3])
            print("\n")
            #input()

        else:
            # If the terminals have not been accessed yet, append the current node at the end of the queue
            queue.append(curr)

    return circuit

def main():
    # **************************************************************************************************************** #
    # NOTE: UI code; Does not contain anything about the actual simulation

    # Used for file access
    script_dir = os.path.dirname(__file__)  # <-- absolute dir the script is in

    print("Circuit Simulator:")

    # Select circuit benchmark file, default is circuit.bench
    while True:
        cktFile = "circuit.bench"
        print("\n Read circuit benchmark file: use " + cktFile + "?" + " Enter to accept or type filename: ")
        userInput = input()
        if userInput == "":
            break
        else:
            cktFile = os.path.join(script_dir, userInput)
            if not os.path.isfile(cktFile):
                print("File does not exist. \n")
            else:
                break

    print("\n Reading " + cktFile + " ... \n")
    circuit = netRead(cktFile)
    print("\n Finished processing benchmark file and built netlist dictionary: \n")
    # Uncomment the following line, for the neater display of the function and then comment out print(circuit)
    printCkt(circuit)
    #print(circuit)

    # keep an initial copy of the circuit for an easy reset
    newCircuit = circuit

    while True:
        f_listName = "f_list.txt"
        print("\n Write fault list file: use " + f_listName + "?" + " Enter to accept or type filename: ")
        userInput = input()
        if userInput == "":
            break
        else:
            f_listName = os.path.join(script_dir, userInput)
            if not os.path.isfile(f_listName):
                print("File does not exist. \n")
            else:
                break

    # Select input file, default is input.txt
    while True:
        inputName = "input.txt"
        print("\n Read input vector file: use " + inputName + "?" + " Enter to accept or type filename: ")
        userInput = input()
        if userInput == "":

            break
        else:
            inputName = os.path.join(script_dir, userInput)
            if not os.path.isfile(inputName):
                print("File does not exist. \n")
            else:
                break

    # Select output file, default is output.txt
    while True:
        outputName = "fault_sim_result.txt"
        print("\n Write output file: use " + outputName + "?" + " Enter to accept or type filename: ")
        userInput = input()
        if userInput == "":
            break
        else:
            outputName = os.path.join(script_dir, userInput)
            break

    # Note: UI code;
    # **************************************************************************************************************** #

    print("\n *** Simulating the" + inputName + " file and will output in" + outputName + "*** \n")
    fault_listFile = open(f_listName, "r")
    inputFile = open(inputName, "r")
    outputFile = open(outputName, "w")
    outputFile.write("# fault sim result \n# input: " + cktFile + " \n# input: " + f_listName + " \n# input: " + inputName + "\n\n")

    # fault parsing for each line of the f_list
    f_list = []
    for fault_line in fault_listFile:

        # For empty lines, ...
        if (fault_line == "\n"):
            continue
        # For any comments
        if (fault_line[0] == "#"):
            continue

        extra = [False]
        # Removing the the newlines at the end and then output it to the txt file
        fault_line= fault_line.replace("\n", "")

        extra.append(fault_line.split("-"))
        f_list.append(extra)

    tv= 1
    # Runs for each line of the input file
    for line in inputFile:
        # Initialization of output variable
        output = ""

        # Do nothing else if empty lines, ...
        if (line == "\n"):
            continue
        # ... or any comments
        if (line[0] == "#"):
            continue

        # for output generation
        line = line.replace("\n", "")
        outputFile.write("tv" + str(tv) + " = " + line)
        tv += 1

        # Removing spaces
        line = line.replace(" ", "")

        print("\n before processing circuit dictionary...")
        #print(circuit)
        print("\n ---> Now ready to simulate INPUT = " + line)
        circuit = inputRead(circuit, line)
        # Uncomment the following line, for the neater display of the function and then comment out print(circuit)
        printCkt(circuit)
        #print(circuit)

        if circuit == -1:
            print("INPUT ERROR: INSUFFICIENT BITS")
            outputFile.write(" -> INPUT ERROR: INSUFFICIENT BITS" + "\n")
            # After each input line is finished, reset the netList
            circuit = newCircuit
            print("...move on to next input\n")
            continue
        elif circuit == -2:
            print("INPUT ERROR: INVALID INPUT VALUE/S")
            outputFile.write(" -> INPUT ERROR: INVALID INPUT VALUE/S" + "\n")
            # After each input line is finished, reset the netList
            circuit = newCircuit
            print("...move on to next input\n")
            continue

        circuit = basic_sim(circuit)
        print("\n *** Finished simulation - resulting circuit: \n")
        # Uncomment the following line, for the neater display of the function and then comment out print(circuit)
        printCkt(circuit)
        #print(circuit)

        for y in circuit["OUTPUTS"][1]:
            if not circuit[y][2]:
                output = "NETLIST ERROR: OUTPUT LINE \"" + y + "\" NOT ACCESSED"
                break
            output = str(circuit[y][3]) + output

        print("\n *** Summary of simulation: ")
        print(line + " -> " + output + " written into output file. \n")
        outputFile.write(" -> " + output + " (good)\ndetected:\n")

        print("\n *** Running the Fault Test... \n")

        for fault in f_list:
            circuit_fault = copy.deepcopy(circuit)

            for key in circuit_fault:
                if (key[0:5] == "wire_"):
                    circuit_fault[key][2] = False
                    circuit_fault[key][3] = 'U'

            circuit_fault = inputRead(circuit_fault, line)

            if(fault[1][1] == "IN"):
                circuit_fault["faultWire"] = ["FAULT", "NONE", True, fault[1][4]]

                for key in circuit_fault:

                    if(fault[1][0] == key[5:]):
                        point = 0
                        for Input in circuit_fault[key][1]:

                            if(fault[1][2] == Input[5:]):
                                circuit_fault[key][1][point] = "faultWire"

                            point += 1
                circuit_fault = basic_sim(circuit_fault)

            elif(fault[1][1] == "SA"):
                linespliced=fault[1]
                circuit_fault=basic_sim(circuit_fault,linespliced)


            fault_out = ""
            for y in circuit_fault["OUTPUTS"][1]:

                if circuit_fault[y][2] == False:
                    output_fault = "NETLIST ERROR: OUTPUT LINE \"" + y + "\" NOT ACCESSED"
                    break
                fault_out = str(circuit_fault[y][3]) + fault_out

            if(output != fault_out):

                if(fault[1][1] == "IN"):

                    outputFile.write(fault[1][0] + "-" + fault[1][1] + "-" + fault[1][2] + "-" + fault[1][3] + "-" + fault[1][4] + ": ")

                    outputFile.write(line + " -> " + fault_out + "\n")

                elif(fault[1][1] == "SA"):

                    outputFile.write(fault[1][0] + "-" + fault[1][1] + "-" + fault[1][2] + ": ")
                    outputFile.write(line + " -> " + fault_out + "\n")

                fault[0] = True


        outputFile.write("\n")
        print("\n *** Now resetting circuit back to unknowns... \n")

        for key in circuit:

            if (key[0:5]=="wire_"):
                circuit[key][2] = False
                circuit[key][3] = 'U'

        print("\n circuit after resetting: \n")
        # Uncomment the following line, for the neater display of the function and then comment out print(circuit)
        printCkt(circuit)
        #print(circuit)

        print("\n*******************\n")

    num_faults = len(f_list)
    undetected_faults = 0

    for fault_line in f_list:
        if(fault_line[0] == False):
            undetected_faults += 1

    detected_faults = num_faults - undetected_faults

    outputFile.write("total detected faults: " + str(detected_faults))
    outputFile.write("\n\nundetected faults: " + str(undetected_faults) + "\n")

    for fault_line in f_list:

        if(fault_line[0] == False):

            if(fault_line[1][1] == "IN"):

                outputFile.write(fault_line[1][0] + "-" + fault_line[1][1] + "-" + fault_line[1][2] + "-" + fault_line[1][3] + "-" + fault_line[1][4] + "\n")

            elif(fault_line[1][1] == "SA"):

                outputFile.write(fault_line[1][0] + "-" + fault_line[1][1] + "-" + fault_line[1][2] + "\n")

    per=str((detected_faults/num_faults)*100 )+"%"
    faultcoverage="\nfault coverage: " + str(detected_faults) + "/" + str(num_faults) + " = " + per
    outputFile.write(faultcoverage)
    outputFile.close()

if __name__ == "__main__":
    main()
