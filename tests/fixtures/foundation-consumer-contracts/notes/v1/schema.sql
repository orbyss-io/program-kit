-- Disposable qualification database only. No consumer migration or database is modified.
CREATE TABLE notes (
  issuer text COLLATE "C" NOT NULL, subject text COLLATE "C" NOT NULL, id uuid NOT NULL,
  revision bigint NOT NULL CHECK (revision > 0), name text NOT NULL,
  CONSTRAINT pk_notes PRIMARY KEY (issuer, subject, id)
);
CREATE TABLE note_revisions (
  issuer text COLLATE "C" NOT NULL, subject text COLLATE "C" NOT NULL, id uuid NOT NULL,
  revision bigint NOT NULL CHECK (revision > 0), name text NOT NULL,
  CONSTRAINT pk_note_revisions PRIMARY KEY (issuer, subject, id, revision),
  CONSTRAINT uq_note_revision_snapshot UNIQUE (issuer, subject, id, revision, name),
  CONSTRAINT fk_revision_note FOREIGN KEY (issuer,subject,id) REFERENCES notes(issuer,subject,id)
);
-- This native deferred cycle admits atomic head+history writes while preventing
-- a committed head from naming an absent or different historical snapshot.
ALTER TABLE notes ADD CONSTRAINT fk_note_head_snapshot
  FOREIGN KEY (issuer,subject,id,revision,name)
  REFERENCES note_revisions(issuer,subject,id,revision,name)
  DEFERRABLE INITIALLY DEFERRED;
CREATE TABLE note_receipts (
  issuer text COLLATE "C" NOT NULL, subject text COLLATE "C" NOT NULL, operation_id uuid NOT NULL,
  digest text NOT NULL CHECK (length(digest) = 64), id uuid NOT NULL, revision bigint NOT NULL, name text NOT NULL,
  CONSTRAINT pk_note_receipts PRIMARY KEY (issuer,subject,operation_id),
  CONSTRAINT fk_receipt_revision FOREIGN KEY (issuer,subject,id,revision,name)
    REFERENCES note_revisions(issuer,subject,id,revision,name)
);
