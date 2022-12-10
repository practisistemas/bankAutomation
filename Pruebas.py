antiguas=[300.00,100.00,200.00,400.00,400.00]
nueva=   [500.00,300.00,100.00,200.00,400.00]


antiguas_result = []
for antiguas_item in antiguas:
    if antiguas_item not in antiguas_result:
        antiguas_result.append(antiguas_item)

#print(antiguas_result)

nueva_result = []
for nueva_item in nueva:
    if nueva_item not in nueva_result:
        nueva_result.append(nueva_item)

#print(nueva_result)

for item in nueva_result:
    count_antiguas =antiguas.count(item)
    count_nueva = nueva.count(item)

    #print(count_antiguas)
    #print(count_nueva)

    if(count_antiguas==count_nueva):
        print("El item Existe: ", item)
    else:
        resultado=count_nueva-count_antiguas
        if resultado<=-1:
            print("Ya existe ")
        else:
            print("El item no Existe: ", item)
            print(resultado)












"""for i in range(5):
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
            print("insertando"+str(nueva[i+j]))
            break
        if Salir ==1:
            break"""