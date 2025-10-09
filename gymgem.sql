CREATE TABLE status(
    id SMALLSERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    description VARCHAR(255),
    type ENUM('user') NOT NULL
);

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50),
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status INT,
    last_seen TIMESTAMP,
    default_profile INT,
    CONSTRAINT fk_user_status FOREIGN KEY(status) REFERENCES status(id)
);

CREATE TABLE mankind_users(
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_picture VARCHAR(255),
    birthdate DATE,
    gender ENUM('m','f'),
    balance DECIMAL(10,2) DEFAULT 0,
    country VARCHAR(50),
    state VARCHAR(50),
    zip_code VARCHAR(20),
    type ENUM('trainer' , 'trainee') NOT NULL,
);

CREATE TABLE roles(
    id SMALLSERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    description VARCHAR(255)
);

CREATE TABLE payment_methods(
    id SMALLSERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    description VARCHAR(255)
);

CREATE TABLE admins(
    id SMALLSERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50),
    email VARCHAR(100) UNIQUE NOT NULL,
    date_of_birth DATE,
    profile_picture VARCHAR(255),
    gender ENUM('m','f'),
    hired_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    password VARCHAR(255) NOT NULL,
    country VARCHAR(50),
    city VARCHAR(50),
    state VARCHAR(50),
    street VARCHAR(100),
    zip_code VARCHAR(20),
    role_id INT,
    CONSTRAINT fk_admin_role FOREIGN KEY(role_id) REFERENCES roles(id)
);

CREATE TABLE admin_phones(
    admin_id INT,
    phone_number VARCHAR(20),
    PRIMARY KEY(admin_id, phone_number),
    CONSTRAINT fk_admin_phone FOREIGN KEY(admin_id) REFERENCES admins(id)
);

CREATE TABLE sizes(
    id SMALLSERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    description VARCHAR(255),
    type ENUM('clothes', 'shoes','weight' ,'volume') NOT NULL
);

CREATE TABLE stores(
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_picture VARCHAR(255),
    name VARCHAR(100) NOT NULL,
    description VARCHAR(255),
    store_type ENUM('supplements', 'clothes', 'both') NOT NULL
);

CREATE TABLE store_branches(
    id SERIAL PRIMARY KEY,
    store_id INT,
    opening_time TIME,
    closing_time TIME,
    country VARCHAR(50),
    state VARCHAR(50),
    street VARCHAR(100),
    zip_code VARCHAR(20),
    CONSTRAINT fk_store_branch_store FOREIGN KEY(store_id) REFERENCES stores(id)
);

CREATE TABLE gyms(
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_picture VARCHAR(255),
    name VARCHAR(100) NOT NULL,
    description VARCHAR(255),
    status INT,
    CONSTRAINT fk_gym_status FOREIGN KEY(status) REFERENCES status(id)
);

CREATE TABLE gym_branches(
    id SERIAL PRIMARY KEY,
    gym_id INT,
    country VARCHAR(50),
    state VARCHAR(50),
    street VARCHAR(100),
    zip_code VARCHAR(20),
    CONSTRAINT fk_gym_branch_gym FOREIGN KEY(gym_id) REFERENCES gyms(id)
);

CREATE TABLE gym_slots(
    id SERIAL PRIMARY KEY,
    gym_id INT,
    branch_id INT,
    gender ENUM('m','f','mix') NOT NULL,
    opening_time TIME,
    closing_time TIME,
    CONSTRAINT fk_gym_slot_gym FOREIGN KEY(gym_id) REFERENCES gyms(id),
    CONSTRAINT fk_gym_slot_branch FOREIGN KEY(branch_id) REFERENCES gym_branches(id)
);

CREATE TABLE services(
    id SMALLSERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description VARCHAR(255),
    fees DECIMAL(10,2) NOT NULL
);

CREATE TABLE packages(
    id SMALLSERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description VARCHAR(255),
    discount tinyint DEFAULT 0,
    duration INTERVAL NOT NULL
);


CREATE TABLE gym_services(
    gym_id INT,
    service_id INT,
    branch_id INT,
    PRIMARY KEY(gym_id, service_id, branch_id),
    CONSTRAINT fk_gym_service_gym FOREIGN KEY(gym_id) REFERENCES gyms(id),
    CONSTRAINT fk_gym_service_service FOREIGN KEY(service_id) REFERENCES services(id),
    CONSTRAINT fk_gym_service_branch FOREIGN KEY(branch_id) REFERENCES gym_branches(id)
);

CREATE TABLE user_profiles(
    id SERIAL PRIMARY KEY,
    
)

CREATE TABLE invoices(
    id SERIAL PRIMARY KEY,
    payer_profile_id UUID,
    recipient_profile_id UUID,
    payment_method_code TINYINT,
    status TINYINT,
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    amount DECIMAL(10,2) NOT NULL,
    note VARCHAR(255),
    CONSTRAINT fk_invoice_payer FOREIGN KEY(payer_profile_id) REFERENCES user_profiles(profile_id),
    CONSTRAINT fk_invoice_recipient FOREIGN KEY(recipient_profile_id) REFERENCES user_profiles(profile_id),
    CONSTRAINT fk_invoice_payment_method FOREIGN KEY(payment_method_code) REFERENCES payment_methods(id)
);


