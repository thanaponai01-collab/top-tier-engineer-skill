# Notes

- `POST /notes` with a non-empty `title` returns 201 and the note; the note is stored and
  `GET /notes` lists it afterwards.
- `POST /notes` with an empty title returns 400 and stores nothing.
