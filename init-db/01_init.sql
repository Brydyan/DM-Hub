CREATE TABLE IF NOT EXISTS customer_credit_transactions (
    transaction_id SERIAL PRIMARY KEY,
    customer_id VARCHAR(15) NOT NULL,
    age INT,
    annual_income NUMERIC(12, 2),
    credit_score INT,
    loan_amount NUMERIC(12, 2),
    has_defaulted BOOLEAN,
    region VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO customer_credit_transactions 
(customer_id, age, annual_income, credit_score, loan_amount, has_defaulted, region) 
VALUES
('CUST-1001', 34, 45000.00, 710, 12000.00, FALSE, 'Costa'),
('CUST-1002', 45, 82000.50, 680, 25000.00, FALSE, 'Sierra'),
('CUST-1003', NULL, 15000.00, 520, 5000.00, TRUE, 'Costa'),
('CUST-1004', 29, 32000.00, 615, 8500.00, FALSE, 'Oriente'),
('CUST-1005', 52, NULL, 790, 40000.00, FALSE, 'Sierra'),
('CUST-1006', 23, 18500.00, 580, 3500.00, TRUE, 'Costa'),
('CUST-1007', 41, 62000.00, 740, 18000.00, FALSE, 'Costa'),
('CUST-1008', 60, 95000.00, NULL, 15000.00, FALSE, 'Insular'),
('CUST-1009', 38, 51000.00, 645, 11000.00, TRUE, 'Sierra');