
# Documentazione API Match Day

Questa è la documentazione per l'API Match Day, un backend per la gestione di giocatori, partite e statistiche di un campionato.

## Panoramica

L'API è costruita con FastAPI e SQLAlchemy. Fornisce endpoint per le operazioni CRUD (Create, Read, Update, Delete) sulle seguenti risorse:

*   **Players**: Gestione dei giocatori e delle loro abilità.
*   **Partite**: Gestione delle partite.
*   **Formazioni**: Gestione delle formazioni per ogni partita.
*   **Gol**: Registrazione dei gol segnati in ogni partita.
*   **Statistics**: Statistiche generali sui giocatori.

## Autenticazione

L'API attualmente non richiede autenticazione, ma è una funzionalità che potrebbe essere aggiunta in futuro.

---

## Endpoints

### Root

#### GET /

Endpoint di base per verificare che l'API sia in funzione.

*   **Metodo**: `GET`
*   **URL**: `/`
*   **Risposta di successo (200 OK)**:
    ```json
    {
      "message": "Match Day API",
      "version": "1.0.0"
    }
    ```

### Health Check

#### GET /health

Endpoint per il monitoraggio dello stato di salute dell'applicazione.

*   **Metodo**: `GET`
*   **URL**: `/health`
*   **Risposta di successo (200 OK)**:
    ```json
    {
      "status": "healthy",
      "environment": "development",
      "database": "connected"
    }
    ```

---

### Players

#### GET /api/players

Recupera un elenco di giocatori.

*   **Metodo**: `GET`
*   **URL**: `/api/players`
*   **Parametri di query**:
    *   `skip` (opzionale, intero, default: 0): Numero di giocatori da saltare.
    *   `limit` (opzionale, intero, default: 100): Numero massimo di giocatori da restituire.
    *   `role` (opzionale, stringa): Filtra i giocatori per ruolo (es. `GOALKEEPER`, `DEFENDER`, `MIDFIELDER`, `FORWARD`).
*   **Risposta di successo (200 OK)**:
    ```json
    [
      {
        "id": "uuid-string",
        "name": "Lionel Messi",
        "role": "FORWARD",
        "photo_url": "http://example.com/photo.jpg",
        "skills": {
          "speed": 10,
          "passing": 9,
          "attack": 10,
          "defense": 4,
          "technique": 10,
          "goalkeeping": 1,
          "heading": 7,
          "stamina": 8,
          "leadership": 9
        },
        "created_at": "2025-07-15T10:00:00Z",
        "updated_at": "2025-07-15T10:00:00Z",
        "goals_scored": 800,
        "assists": 350,
        "gold_medals": 1,
        "silver_medals": 1,
        "bronze_medals": 0
      }
    ]
    ```

#### GET /api/players/{player_id}

Recupera i dettagli di un singolo giocatore.

*   **Metodo**: `GET`
*   **URL**: `/api/players/{player_id}`
*   **Parametri di percorso**:
    *   `player_id` (stringa, obbligatorio): L'ID del giocatore.
*   **Risposta di successo (200 OK)**:
    ```json
    {
      "id": "uuid-string",
      "name": "Lionel Messi",
      "role": "FORWARD",
      "photo_url": "http://example.com/photo.jpg",
      "skills": {
        "speed": 10,
        "passing": 9,
        "attack": 10,
        "defense": 4,
        "technique": 10,
        "goalkeeping": 1,
        "heading": 7,
        "stamina": 8,
        "leadership": 9
      },
      "created_at": "2025-07-15T10:00:00Z",
      "updated_at": "2025-07-15T10:00:00Z",
      "overall_rating": 95,
      "goals_scored": 800,
      "assists": 350,
      "gold_medals": 1,
      "silver_medals": 1,
      "bronze_medals": 0
    }
    ```
*   **Risposta di errore (404 Not Found)**:
    ```json
    {
      "detail": "Player not found"
    }
    ```

#### POST /api/players

Crea un nuovo giocatore.

*   **Metodo**: `POST`
*   **URL**: `/api/players`
*   **Corpo della richiesta**:
    ```json
    {
      "name": "Kylian Mbappé",
      "role": "FORWARD",
      "skills": {
        "speed": 10,
        "passing": 8,
        "attack": 9,
        "defense": 4,
        "technique": 9,
        "goalkeeping": 1,
        "heading": 7,
        "stamina": 9,
        "leadership": 7
      }
    }
    ```
*   **Risposta di successo (200 OK)**: Ritorna l'oggetto del giocatore creato.

#### PUT /api/players/{player_id}

Aggiorna i dati di un giocatore esistente.

*   **Metodo**: `PUT`
*   **URL**: `/api/players/{player_id}`
*   **Parametri di percorso**:
    *   `player_id` (stringa, obbligatorio): L'ID del giocatore.
*   **Corpo della richiesta**:
    ```json
    {
      "name": "Kylian Mbappé Lottin",
      "skills": {
        "leadership": 8
      }
    }
    ```
*   **Risposta di successo (200 OK)**: Ritorna l'oggetto del giocatore aggiornato.
*   **Risposta di errore (404 Not Found)**:
    ```json
    {
      "detail": "Player not found"
    }
    ```

#### DELETE /api/players/{player_id}

Elimina un giocatore.

*   **Metodo**: `DELETE`
*   **URL**: `/api/players/{player_id}`
*   **Parametri di percorso**:
    *   `player_id` (stringa, obbligatorio): L'ID del giocatore.
*   **Risposta di successo (200 OK)**:
    ```json
    {
      "message": "Player deleted successfully"
    }
    ```
*   **Risposta di errore (404 Not Found)**:
    ```json
    {
      "detail": "Player not found"
    }
    ```

#### POST /api/players/{player_id}/photo

Carica una foto per un giocatore.

*   **Metodo**: `POST`
*   **URL**: `/api/players/{player_id}/photo`
*   **Parametri di percorso**:
    *   `player_id` (stringa, obbligatorio): L'ID del giocatore.
*   **Corpo della richiesta**: Dati del file immagine (`multipart/form-data`).
*   **Risposta di successo (200 OK)**:
    ```json
    {
      "photo_url": "http://example.com/new_photo.jpg",
      "message": "Photo uploaded successfully"
    }
    ```
*   **Risposta di errore (404 Not Found)**:
    ```json
    {
      "detail": "Player not found"
    }
    ```

---

### Partite

#### POST /api/partite

Crea una nuova partita.

*   **Metodo**: `POST`
*   **URL**: `/api/partite`
*   **Corpo della richiesta**:
    ```json
    {
      "data_partita": "2025-08-01",
      "ora_inizio": "21:00:00",
      "nome_squadra_a": "Squadra A",
      "nome_squadra_b": "Squadra B",
      "stadio": "Stadio Olimpico"
    }
    ```
*   **Risposta di successo (200 OK)**: Ritorna l'oggetto della partita creata.

#### GET /api/partite

Recupera un elenco di partite.

*   **Metodo**: `GET`
*   **URL**: `/api/partite`
*   **Parametri di query**:
    *   `skip` (opzionale, intero, default: 0): Numero di partite da saltare.
    *   `limit` (opzionale, intero, default: 100): Numero massimo di partite da restituire.
*   **Risposta di successo (200 OK)**: Ritorna un array di oggetti partita.

#### GET /api/partite/{partita_id}

Recupera i dettagli di una singola partita.

*   **Metodo**: `GET`
*   **URL**: `/api/partite/{partita_id}`
*   **Parametri di percorso**:
    *   `partita_id` (intero, obbligatorio): L'ID della partita.
*   **Risposta di successo (200 OK)**: Ritorna l'oggetto della partita.
*   **Risposta di errore (404 Not Found)**:
    ```json
    {
      "detail": "Partita not found"
    }
    ```

#### PUT /api/partite/{partita_id}

Aggiorna i dati di una partita.

*   **Metodo**: `PUT`
*   **URL**: `/api/partite/{partita_id}`
*   **Parametri di percorso**:
    *   `partita_id` (intero, obbligatorio): L'ID della partita.
*   **Corpo della richiesta**:
    ```json
    {
      "gol_squadra_a": 1,
      "gol_squadra_b": 0
    }
    ```
*   **Risposta di successo (200 OK)**: Ritorna l'oggetto della partita aggiornato.
*   **Risposta di errore (404 Not Found)**:
    ```json
    {
      "detail": "Partita not found"
    }
    ```

#### DELETE /api/partite/{partita_id}

Elimina una partita.

*   **Metodo**: `DELETE`
*   **URL**: `/api/partite/{partita_id}`
*   **Parametri di percorso**:
    *   `partita_id` (intero, obbligatorio): L'ID della partita.
*   **Risposta di successo (200 OK)**:
    ```json
    {
      "message": "Partita deleted successfully"
    }
    ```
*   **Risposta di errore (404 Not Found)**:
    ```json
    {
      "detail": "Partita not found"
    }
    ```

---

### Formazioni

#### POST /api/formazioni

Aggiunge uno o più giocatori a una formazione di una partita.

*   **Metodo**: `POST`
*   **URL**: `/api/formazioni`
*   **Corpo della richiesta**: Un array di oggetti formazione.
    ```json
    [
      {
        "partita_id": 1,
        "giocatore_id": "uuid-string-1",
        "squadra": "A",
        "numero_maglia": 10
      },
      {
        "partita_id": 1,
        "giocatore_id": "uuid-string-2",
        "squadra": "B",
        "numero_maglia": 9
      }
    ]
    ```
*   **Risposta di successo (200 OK)**: Ritorna un array degli oggetti formazione creati.

#### GET /api/partite/{partita_id}/formazioni

Ottieni le formazioni per una specifica partita.

*   **Metodo**: `GET`
*   **URL**: `/api/partite/{partita_id}/formazioni`
*   **Parametri di percorso**:
    *   `partita_id` (intero, obbligatorio): L'ID della partita.
*   **Risposta di successo (200 OK)**: Ritorna un array di oggetti formazione con i dettagli dei giocatori.

#### PUT /api/partite/{partita_id}/formazioni

Aggiorna tutte le formazioni di una partita (sostituisce completamente la formazione esistente).

*   **Metodo**: `PUT`
*   **URL**: `/api/partite/{partita_id}/formazioni`
*   **Parametri di percorso**:
    *   `partita_id` (intero, obbligatorio): L'ID della partita.
*   **Corpo della richiesta**: Un array di oggetti formazione.
    ```json
    [
      {
        "partita_id": 1,
        "giocatore_id": "uuid-string-1",
        "squadra": "A",
        "numero_maglia": 10,
        "capitano": true
      },
      {
        "partita_id": 1,
        "giocatore_id": "uuid-string-2",
        "squadra": "B",
        "numero_maglia": 9,
        "capitano": false
      }
    ]
    ```
*   **Risposta di successo (200 OK)**: Ritorna un array degli oggetti formazione aggiornati.
*   **Risposta di errore (404 Not Found)**:
    ```json
    {
      "detail": "Partita not found"
    }
    ```
*   **Risposta di errore (400 Bad Request)**: Se il `partita_id` nel body non corrisponde a quello nell'URL o se un giocatore non esiste.
    ```json
    {
      "detail": "partita_id in body (2) must match URL parameter (1)"
    }
    ```

---

### Gol

#### POST /api/gol

Registra un gol.

*   **Metodo**: `POST`
*   **URL**: `/api/gol`
*   **Corpo della richiesta**:
    ```json
    {
      "partita_id": 1,
      "giocatore_id": "uuid-string-1",
      "minuto": 75,
      "squadra": "A",
      "tipo_gol": "NORMALE"
    }
    ```
*   **Risposta di successo (200 OK)**: Ritorna l'oggetto del gol creato.

#### GET /api/gol

Recupera un elenco di tutti i gol registrati.

*   **Metodo**: `GET`
*   **URL**: `/api/gol`
*   **Parametri di query**:
    *   `skip` (opzionale, intero, default: 0): Numero di gol da saltare.
    *   `limit` (opzionale, intero, default: 100): Numero massimo di gol da restituire.
*   **Risposta di successo (200 OK)**: Ritorna un array di oggetti gol.

#### GET /api/gol/{gol_id}

Recupera i dettagli di un singolo gol.

*   **Metodo**: `GET`
*   **URL**: `/api/gol/{gol_id}`
*   **Parametri di percorso**:
    *   `gol_id` (intero, obbligatorio): L'ID del gol.
*   **Risposta di successo (200 OK)**: Ritorna l'oggetto del gol.
*   **Risposta di errore (404 Not Found)**:
    ```json
    {
      "detail": "Gol not found"
    }
    ```

#### GET /api/partite/{partita_id}/gol

Recupera tutti i gol di una partita specifica.

*   **Metodo**: `GET`
*   **URL**: `/api/partite/{partita_id}/gol`
*   **Parametri di percorso**:
    *   `partita_id` (intero, obbligatorio): L'ID della partita.
*   **Risposta di successo (200 OK)**: Ritorna un array di oggetti gol per la partita specificata.
*   **Risposta di errore (404 Not Found)**:
    ```json
    {
      "detail": "Partita not found"
    }
    ```

#### DELETE /api/gol/{gol_id}

Elimina un gol registrato.

*   **Metodo**: `DELETE`
*   **URL**: `/api/gol/{gol_id}`
*   **Parametri di percorso**:
    *   `gol_id` (intero, obbligatorio): L'ID del gol.
*   **Risposta di successo (200 OK)**:
    ```json
    {
      "message": "Gol deleted successfully"
    }
    ```
*   **Risposta di errore (404 Not Found)**:
    ```json
    {
      "detail": "Gol not found"
    }
    ```

---

### Statistics

#### GET /api/statistics

Ottieni statistiche generali.

*   **Metodo**: `GET`
*   **URL**: `/api/statistics`
*   **Risposta di successo (200 OK)**:
    ```json
    {
      "total_players": 50,
      "players_by_role": {
        "GOALKEEPER": 5,
        "DEFENDER": 15,
        "MIDFIELDER": 20,
        "FORWARD": 10
      },
      "average_skills": {
        "speed": 7.5,
        "passing": 8.1,
        "attack": 7.9,
        "defense": 6.5,
        "technique": 8.2,
        "goalkeeping": 2.3,
        "heading": 6.8,
        "stamina": 7.7,
        "leadership": 7.2
      }
    }
    ```
