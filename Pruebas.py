import numpy as np

a = np.array([200.00,200.00,300.00,300.00,100.00])
b = np.array([300.00,100.00,200.00,400.00,400.00])

c = np.setdiff1d(a, b)
print(c)













nueva=   [200.00,600.00,300.00,900.00,200.00]
antiguas=[300.00,100.00,200.00,400.00,400.00]

for i in range(5):
    NoSonIguales = 0
    Salir = 0
    for j in range(5):
        try:
            nueva[i+j]
        except IndexError:
            Salir=1
            break
        if Salir==1:
            break
        if nueva[i+j]!=antiguas[j]:
            NoSonIguales  = 1
            print("insertando"+str(nueva[i+j]));
            break

        if Salir ==1:
            break





array1=[400.00,500.00,300.00,100.00,200.00] #Nuevas
array2=[300.00,100.00,200.00,400.00,400.00] #Antiguas



# Combine the arrays into a list of tuples using the zip function
combined_arrays = zip(array1, array2)

# Print the combined arrays
print(list(combined_arrays))
# Output: [(1, 3), (2, 4), (3, 5), (4, 6), (5, 7)]

# Find matching elements in the combined arrays
for a, b in combined_arrays:
    if a == b+2:
        print(f"Matching element: {a}")
# Output:
# Matching element: 3
# Matching element: 4
# Matching element: 5









