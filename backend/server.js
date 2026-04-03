require('dotenv').config();
const app = require('./app');
const prisma = require('./config/db');

const PORT = process.env.PORT || 5000;

const startServer = async () => {
  try {
    // Basic DB connection check
    await prisma.$connect();
    console.log('Connected to Database');

    app.listen(PORT, () => {
      console.log(`Server is running on port ${PORT}`);
    });
  } catch (err) {
    console.error('Server connection error:', err);
    process.exit(1);
  }
};

startServer();
