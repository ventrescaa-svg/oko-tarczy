# „Klasówka”: stały sprawdzian modelu AI grota (zalecenie 3 z audytu 2026-10-26, zgoda Piotra 2026-10-31).
# Co czwarta tura rzucona po nauce modelu v3 trafia do klasówki na zawsze: model nigdy się na niej nie uczy,
# a każdy nowy model jest na niej porównywany ze starym. Wybór zależy tylko od czasu tury (ts próbki, wspólny
# dla 3 rzutek tury), więc ten sam rzut jest zawsze po tej samej stronie, w każdym rozpakowaniu i na każdym komputerze.
# Użycie: python3 klasowka.py katalog_z_rozpakuj   (ile rzutów jest w klasówce)
import hashlib, json, sys

KL_OD = 1793305417908   # ts ostatniej próbki w paczce 20261029-2123-ejwn (ostatnia w nauce modelu v3, ?v=3)
KL_CO = 4               # co która tura

def w_klasowce(s):
    ts = s.get('ts')
    if not ts or ts <= KL_OD: return False
    return int(hashlib.sha1(str(ts).encode()).hexdigest(), 16) % KL_CO == 0

if __name__ == '__main__':
    S = json.load(open(sys.argv[1] + '/manifest.json'))['samples']
    k = [s for s in S if w_klasowce(s)]
    src = lambda L, x: sum(s['label']['source'] == x for s in L)
    print(f'próbek {len(S)}, po nauce v3 {sum(s.get("ts", 0) > KL_OD for s in S)}, w klasówce {len(k)} '
          f'(stuknięte {src(k, "tap")}, potwierdzone {src(k, "confirmed")}, auto {src(k, "auto")})')
