-- Explicit disposable application deployment migration; never part of generic readiness.
CREATE TABLE owned_resource (id uuid PRIMARY KEY, issuer text NOT NULL, subject text NOT NULL);
