
#nueva=   [900.00,200.00,200.00,400.00,400.00]
#antiguas_SQL=[900.00,200.00,200.00,400.00,400.00]

nueva=       [900.00,100.00, 100.00, 0.16, 300.00, 100.00, 200.00, 200.00, 250.00, 100.00, 110.00, 100.00, 100.00, 0.01, 0.03, -200000000.00, -300000000.00, 200000000.00, 300000000.00, 100.00]
antiguas_SQL=[100.00, 0.16, 300.00, 100.00, 200.00, 200.00, 250.00, 100.00, 110.00, 100.00, 100.00, 0.01, 0.03, -200000000.00, -300000000.00, 200000000.00, 300000000.00, 100.00, 3279.56, -230.00]

print(type(nueva))
print(type(antiguas_SQL))

for i in range(len(antiguas_SQL)):
    NoSonIguales = 0
    Salir = 0
    for j in range(len(antiguas_SQL)):
        print(i," ",j)
        try:
            nueva[i + j]
        except IndexError:
            Salir = 1
            break
        if Salir == 1:
            break
        if nueva[i + j] != antiguas_SQL[j]:
            NoSonIguales = 1
            print("insertando: " + str(nueva[i]))
            break

        if Salir == 1:
            break
    if Salir == 1:
        break
    if NoSonIguales == 0:
        break














