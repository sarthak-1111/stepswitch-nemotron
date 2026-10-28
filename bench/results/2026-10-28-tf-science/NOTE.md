# A run that could not start

The first mini-science run of the Nemotron ladder against Nemotron 3 Ultra alone. Every run
ended at once with `no_worker`: science tasks run offline by default (SPEC §6), so no hosted
model was eligible, and no model was called ($0.00). The bench policy for Token Factory
(`bench/policies/tokenfactory-ladder.toml`) now lets the suite's toy science tasks use hosted
models. Kept for the record, not as evidence; the complete run is `2026-10-28-tf-mini-science`.
