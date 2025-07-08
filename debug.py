# local
#from processes.brl_drainage import mainHandler
from processes.brl_watersystem import mainHandler

def main():
    #f = r'test_drainage.geojson'
    f = r'test_watersystem.geojson'
    with open(f, 'r') as file:
        json_input = file.read().replace('\n','')

    res = mainHandler(json_input)

if __name__ == '__main__':
    main()