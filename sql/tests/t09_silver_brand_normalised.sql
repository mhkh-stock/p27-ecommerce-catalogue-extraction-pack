-- t09: no raw first-word sub-brand may survive in silver.brand.
SELECT product_id, brand
FROM silver_catalogue
WHERE brand IN ('ThinkPad', 'Aspire', 'Galaxy', 'Hewlett', 'Pavilion',
                'ProBook', 'Inspiron', 'IdeaTab', 'Iphone', 'iPad',
                'Iconia', 'Memo', 'MeMO', 'MeMo', 'Packard');
