const bcrypt = require('bcrypt');
const prisma = require('../config/db');
const { generateAccessToken, generateRefreshToken } = require('../config/jwt');

class AuthService {
  async register(username, email, password) {
    const hashedPassword = await bcrypt.hash(password, 10);
    return await prisma.user.create({
      data: { username, email, password: hashedPassword, provider: 'local' }
    });
  }

  async login(identifier, password) {
    const user = await prisma.user.findFirst({
      where: {
        OR: [
          { email: identifier },
          { username: identifier }
        ]
      }
    });

    if (!user) return { error: 'User not found' };
    if (user.provider === 'google' && !user.password) return { error: 'Please use Google Login' };

    const isMatch = await bcrypt.compare(password, user.password);
    if (!isMatch) return { error: 'Invalid password' };

    const accessToken = generateAccessToken(user.id);
    const refreshToken = generateRefreshToken(user.id);

    await this.storeToken(user.id, accessToken, refreshToken);

    return { user, accessToken, refreshToken };
  }

  async handleGoogleCallback(user) {
    const accessToken = generateAccessToken(user.id);
    const refreshToken = generateRefreshToken(user.id);

    await this.storeToken(user.id, accessToken, refreshToken);

    return { user, accessToken, refreshToken };
  }

  async refreshToken(token) {
    const prisma = require('../config/db');
    const { verifyRefreshToken } = require('../config/jwt');
    
    try {
      const decoded = verifyRefreshToken(token);
      const oauthRecord = await prisma.oAuth.findFirst({
        where: { refreshToken: token, userId: decoded.userId }
      });

      if (!oauthRecord) return { error: 'Invalid refresh token' };

      const newAccessToken = generateAccessToken(decoded.userId);
      return { accessToken: newAccessToken };
    } catch (err) {
      return { error: 'Token verification failed' };
    }
  }

  async storeToken(userId, accessToken, refreshToken) {
    // Optionally delete old ones if you want single-session or similar. 
    // Here we just store it.
    return await prisma.oAuth.create({
      data: {
        userId,
        accessToken,
        refreshToken,
        expiresAt: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000) // 7 days
      }
    });
  }

  async logout(refreshToken) {
    return await prisma.oAuth.deleteMany({
      where: { refreshToken }
    });
  }
}

module.exports = new AuthService();
