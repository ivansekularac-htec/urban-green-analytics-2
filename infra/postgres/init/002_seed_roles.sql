INSERT INTO urbangreen.roles (
    name,
    description
)
VALUES
    ('Farm Manager', 'Manager responsible for specific farm'),
    ('Operations Team', 'Team responsible for daily farm operations'),
    ('Admin', 'System administrator with full privileges')
ON CONFLICT (name) DO NOTHING;