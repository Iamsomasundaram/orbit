
CREATE TABLE portfolios (
	portfolio_id VARCHAR(128) NOT NULL, 
	portfolio_name VARCHAR(255) NOT NULL, 
	portfolio_type VARCHAR(64) NOT NULL, 
	owner VARCHAR(255) NOT NULL, 
	submitted_at VARCHAR(64) NOT NULL, 
	portfolio_status VARCHAR(32) NOT NULL, 
	latest_review_run_id VARCHAR(128), 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	CONSTRAINT pk_portfolios PRIMARY KEY (portfolio_id)
)

;


CREATE TABLE canonical_portfolios (
	canonical_portfolio_row_id VARCHAR(160) NOT NULL, 
	portfolio_id VARCHAR(128) NOT NULL, 
	schema_version VARCHAR(32) NOT NULL, 
	section_count INTEGER NOT NULL, 
	portfolio_payload_hash VARCHAR(64) NOT NULL, 
	canonical_payload JSONB NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	CONSTRAINT pk_canonical_portfolios PRIMARY KEY (canonical_portfolio_row_id), 
	CONSTRAINT uq_canonical_portfolios_portfolio_id UNIQUE (portfolio_id, schema_version), 
	CONSTRAINT fk_canonical_portfolios_portfolio_id_portfolios FOREIGN KEY(portfolio_id) REFERENCES portfolios (portfolio_id)
)

;


CREATE TABLE review_runs (
	run_id VARCHAR(128) NOT NULL, 
	portfolio_id VARCHAR(128) NOT NULL, 
	review_status VARCHAR(32) NOT NULL, 
	active_backend VARCHAR(32) NOT NULL, 
	reference_runtime VARCHAR(64) NOT NULL, 
	prompt_contract_version VARCHAR(64) NOT NULL, 
	artifact_bundle_hash VARCHAR(64) NOT NULL, 
	started_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	completed_at TIMESTAMP WITH TIME ZONE, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	CONSTRAINT pk_review_runs PRIMARY KEY (run_id), 
	CONSTRAINT fk_review_runs_portfolio_id_portfolios FOREIGN KEY(portfolio_id) REFERENCES portfolios (portfolio_id)
)

;


CREATE TABLE source_documents (
	source_document_row_id VARCHAR(160) NOT NULL, 
	source_document_id VARCHAR(128) NOT NULL, 
	portfolio_id VARCHAR(128) NOT NULL, 
	kind VARCHAR(64) NOT NULL, 
	title VARCHAR(255) NOT NULL, 
	path TEXT NOT NULL, 
	document_hash VARCHAR(64) NOT NULL, 
	content_available BOOLEAN NOT NULL, 
	source_payload JSONB NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	CONSTRAINT pk_source_documents PRIMARY KEY (source_document_row_id), 
	CONSTRAINT uq_source_documents_portfolio_id UNIQUE (portfolio_id, source_document_id), 
	CONSTRAINT fk_source_documents_portfolio_id_portfolios FOREIGN KEY(portfolio_id) REFERENCES portfolios (portfolio_id)
)

;


CREATE TABLE agent_reviews (
	agent_review_row_id VARCHAR(192) NOT NULL, 
	run_id VARCHAR(128) NOT NULL, 
	portfolio_id VARCHAR(128) NOT NULL, 
	agent_id VARCHAR(128) NOT NULL, 
	recommendation VARCHAR(64) NOT NULL, 
	findings_count INTEGER NOT NULL, 
	dimension_count INTEGER NOT NULL, 
	review_payload_hash VARCHAR(64) NOT NULL, 
	review_payload JSONB NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	CONSTRAINT pk_agent_reviews PRIMARY KEY (agent_review_row_id), 
	CONSTRAINT uq_agent_reviews_run_id UNIQUE (run_id, agent_id), 
	CONSTRAINT fk_agent_reviews_run_id_review_runs FOREIGN KEY(run_id) REFERENCES review_runs (run_id), 
	CONSTRAINT fk_agent_reviews_portfolio_id_portfolios FOREIGN KEY(portfolio_id) REFERENCES portfolios (portfolio_id)
)

;


CREATE TABLE audit_events (
	event_id VARCHAR(128) NOT NULL, 
	portfolio_id VARCHAR(128), 
	run_id VARCHAR(128), 
	actor_type VARCHAR(32) NOT NULL, 
	actor_id VARCHAR(128) NOT NULL, 
	display_name VARCHAR(255) NOT NULL, 
	action VARCHAR(128) NOT NULL, 
	entity_type VARCHAR(64) NOT NULL, 
	entity_id VARCHAR(160) NOT NULL, 
	event_payload JSONB NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	CONSTRAINT pk_audit_events PRIMARY KEY (event_id), 
	CONSTRAINT fk_audit_events_portfolio_id_portfolios FOREIGN KEY(portfolio_id) REFERENCES portfolios (portfolio_id), 
	CONSTRAINT fk_audit_events_run_id_review_runs FOREIGN KEY(run_id) REFERENCES review_runs (run_id)
)

;


CREATE TABLE committee_reports (
	run_id VARCHAR(128) NOT NULL, 
	portfolio_id VARCHAR(128) NOT NULL, 
	final_recommendation VARCHAR(64) NOT NULL, 
	report_payload_hash VARCHAR(64) NOT NULL, 
	markdown_sha256 VARCHAR(64) NOT NULL, 
	report_payload JSONB NOT NULL, 
	markdown TEXT NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	CONSTRAINT pk_committee_reports PRIMARY KEY (run_id), 
	CONSTRAINT fk_committee_reports_run_id_review_runs FOREIGN KEY(run_id) REFERENCES review_runs (run_id), 
	CONSTRAINT fk_committee_reports_portfolio_id_portfolios FOREIGN KEY(portfolio_id) REFERENCES portfolios (portfolio_id)
)

;


CREATE TABLE conflicts (
	conflict_row_id VARCHAR(192) NOT NULL, 
	run_id VARCHAR(128) NOT NULL, 
	portfolio_id VARCHAR(128) NOT NULL, 
	conflict_id VARCHAR(128) NOT NULL, 
	conflict_type VARCHAR(64) NOT NULL, 
	topic VARCHAR(255) NOT NULL, 
	severity VARCHAR(32) NOT NULL, 
	conflict_payload_hash VARCHAR(64) NOT NULL, 
	conflict_payload JSONB NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	CONSTRAINT pk_conflicts PRIMARY KEY (conflict_row_id), 
	CONSTRAINT uq_conflicts_run_id UNIQUE (run_id, conflict_id), 
	CONSTRAINT fk_conflicts_run_id_review_runs FOREIGN KEY(run_id) REFERENCES review_runs (run_id), 
	CONSTRAINT fk_conflicts_portfolio_id_portfolios FOREIGN KEY(portfolio_id) REFERENCES portfolios (portfolio_id)
)

;


CREATE TABLE scorecards (
	run_id VARCHAR(128) NOT NULL, 
	portfolio_id VARCHAR(128) NOT NULL, 
	final_recommendation VARCHAR(64) NOT NULL, 
	weighted_composite_score FLOAT NOT NULL, 
	scorecard_payload_hash VARCHAR(64) NOT NULL, 
	scorecard_payload JSONB NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	CONSTRAINT pk_scorecards PRIMARY KEY (run_id), 
	CONSTRAINT fk_scorecards_run_id_review_runs FOREIGN KEY(run_id) REFERENCES review_runs (run_id), 
	CONSTRAINT fk_scorecards_portfolio_id_portfolios FOREIGN KEY(portfolio_id) REFERENCES portfolios (portfolio_id)
)

;

CREATE INDEX ix_review_runs_portfolio_id ON review_runs (portfolio_id);

CREATE INDEX ix_agent_reviews_agent_id ON agent_reviews (agent_id);

CREATE INDEX ix_agent_reviews_run_id ON agent_reviews (run_id);

CREATE INDEX ix_audit_events_entity_type ON audit_events (entity_type);

CREATE INDEX ix_audit_events_portfolio_id ON audit_events (portfolio_id);

CREATE INDEX ix_audit_events_run_id ON audit_events (run_id);

CREATE INDEX ix_conflicts_run_id ON conflicts (run_id);
