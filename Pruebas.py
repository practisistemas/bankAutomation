from datetime import datetime, timedelta
from datetime import date

hoy = date.today()
hora_actual = datetime.now()
print(hoy)
print(hora_actual.hour)
print(hora_actual.minute)
print(hora_actual.second)
folio_number = str(hoy)+"-"+str(hora_actual.hour)+"-"+str(hora_actual.minute)+"-"+str(hora_actual.second)
print(folio_number)

segundos = 14131606

horas = int(segundos / 3600)
segundos -= horas * 3600
minutos = int(segundos / 60)
segundos -= minutos * 60

print("%s:%s:%s" % (horas, minutos, segundos))




















#nueva=   [900.00,200.00,200.00,400.00,400.00]
#antiguas_SQL=[900.00,200.00,200.00,400.00,400.00]

nueva=       ['100.00', '100.00', '100.00', '100.00', '100.00', '100.00', '100.00', '100.00', '0.16', '300.00', '100.00', '200.00', '200.00', '250.00', '100.00', '110.00', '100.00', '100.00', '0.01', '0.03']
antiguas_SQL=['100.00', '100.00', '100.00', '100.00', '100.00', '100.00', '100.00', '100.00', '0.16', '300.00', '100.00', '200.00', '200.00', '250.00', '100.00', '110.00', '100.00', '100.00', '0.01', '0.03']

print(type(nueva))
print(type(antiguas_SQL))

for i in range(15):
    NoSonIguales = 0
    Salir = 0
    for j in range(15):
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
            print("Ingreso")
            break

        if Salir == 1:
            break
    if Salir == 1:
        break
    if NoSonIguales == 0:
        break

print("For de 10  a 1")
for u in range(10,-1, -1):
    print(u)

if 'Hola' in 'Hola Mundo':  # esto nos devolverá False
    print('doce existe en Docena.')
else:
    print('doce no existe en Docena.')









