-- ---------------------------------------------------------------------------
-- Hasierako datuak (PostgreSQL)
--
-- Urkoren dump-a inportatu ondoren, fitxategi hau exekutatu daiteke:
--   psql -U postgres -d powerbank_erreserba -f database/seed.sql
--
-- Behin baino gehiagotan exekutatu daiteke: erregistroak ez dira bikoiztuko.
-- ---------------------------------------------------------------------------

-- ROLAK: derrigorrezkoak dira erabiltzaileak sortu ahal izateko (FK)
INSERT INTO rolak (id_rol, rol_izena) VALUES
    (1, 'Admin'),
    (2, 'Erabiltzaile')
ON CONFLICT (id_rol) DO NOTHING;

-- ERABILTZAILE ADIBIDEA (garapenerako soilik, pasahitza testu lauan)
INSERT INTO erabiltzaileak (nan, izena, abizenak, email, pasahitza, helbidea, id_rol, activo)
SELECT '12345678A', 'Ane', 'Adibide', 'ane@adibide.eus', '123456', 'Kale Nagusia 1', 2, true
WHERE NOT EXISTS (SELECT 1 FROM erabiltzaileak WHERE email = 'ane@adibide.eus');

-- KARGAGUNE ADIBIDEA
INSERT INTO takillak (izena, helbidea, egoera)
SELECT 'Plaza', 'Plaza Nagusia 1', 'erabilgarri'
WHERE NOT EXISTS (SELECT 1 FROM takillak WHERE izena = 'Plaza');

INSERT INTO takillak (izena, helbidea, egoera)
SELECT 'Geltokia', 'Geltoki Etorbidea 2', 'erabilgarri'
WHERE NOT EXISTS (SELECT 1 FROM takillak WHERE izena = 'Geltokia');

-- KARGA-POSTUAK (kargagune bakoitzeko bi, adibidez)
INSERT INTO postuak (id_takilla, egoera)
SELECT t.id_takilla, 'hutsa'
FROM takillak t
WHERE t.izena IN ('Plaza', 'Geltokia')
  AND NOT EXISTS (
      SELECT 1 FROM postuak p WHERE p.id_takilla = t.id_takilla
  );

-- POWERBANKAK postu bakoitzean
INSERT INTO powerbank (id_postu, karga, id_takilla)
SELECT p.id_postu, 100, p.id_takilla
FROM postuak p
JOIN takillak t ON t.id_takilla = p.id_takilla
WHERE t.izena IN ('Plaza', 'Geltokia')
  AND NOT EXISTS (
      SELECT 1 FROM powerbank pb WHERE pb.id_postu = p.id_postu
  );
