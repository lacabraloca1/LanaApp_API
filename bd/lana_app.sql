
-- Crear la base de datos
CREATE DATABASE IF NOT EXISTS lana_app;
USE lana_app;

-- Tabla de usuarios
CREATE TABLE usuarios (
    id_usuario INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    correo VARCHAR(100) NOT NULL UNIQUE,
    telefono VARCHAR(15) NOT NULL UNIQUE,
    contraseña_hash VARCHAR(255) NOT NULL,
    pin_seguridad VARCHAR(10),
    fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de verificación OTP
CREATE TABLE verificacion_otp (
    id_otp INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario INT,
    codigo_otp VARCHAR(6) NOT NULL,
    expira_en DATETIME NOT NULL,
    verificado BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario)
);

-- Tabla de categorías
CREATE TABLE categorias (
    id_categoria INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL UNIQUE,
    tipo ENUM('ingreso', 'egreso') NOT NULL
);

-- Tabla de transacciones
CREATE TABLE transacciones (
    id_transaccion INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario INT,
    tipo ENUM('ingreso', 'egreso', 'envio', 'solicitud') NOT NULL,
    monto DECIMAL(10,2) NOT NULL,
    fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
    descripcion TEXT,
    categoria_id INT,
    destinatario_id INT,
    estado ENUM('pendiente', 'completada', 'cancelada') DEFAULT 'completada',
    FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario),
    FOREIGN KEY (categoria_id) REFERENCES categorias(id_categoria),
    FOREIGN KEY (destinatario_id) REFERENCES usuarios(id_usuario)
);

-- Tabla de presupuestos
CREATE TABLE presupuestos (
    id_presupuesto INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario INT,
    id_categoria INT,
    monto_mensual DECIMAL(10,2) NOT NULL,
    mes INT CHECK (mes BETWEEN 1 AND 12),
    año INT NOT NULL,
    FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario),
    FOREIGN KEY (id_categoria) REFERENCES categorias(id_categoria)
);

-- Tabla de pagos recurrentes
CREATE TABLE pagos_recurrentes (
    id_pago INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario INT,
    id_categoria INT,
    monto DECIMAL(10,2) NOT NULL,
    descripcion VARCHAR(255) NOT NULL,
    frecuencia_dias INT NOT NULL,
    proxima_fecha_pago DATE NOT NULL,
    activo BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario),
    FOREIGN KEY (id_categoria) REFERENCES categorias(id_categoria)
);

-- Tabla de notificaciones
CREATE TABLE notificaciones (
    id_notificacion INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario INT,
    titulo VARCHAR(100) NOT NULL,
    mensaje TEXT NOT NULL,
    tipo ENUM('presupuesto','pago','sistema') NOT NULL,
    fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
    leida BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario)
);

-- Tabla de métodos de recarga
CREATE TABLE metodos_recarga (
    id_metodo INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL,
    activo BOOLEAN DEFAULT TRUE
);

-- Tabla de recargas
CREATE TABLE recargas (
    id_recarga INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario INT,
    id_metodo INT,
    monto DECIMAL(10,2) NOT NULL,
    fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario),
    FOREIGN KEY (id_metodo) REFERENCES metodos_recarga(id_metodo)
);
