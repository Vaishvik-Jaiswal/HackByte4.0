const authService = require('../services/authService');
const passport = require('../config/passport');
const { generateAccessToken, generateRefreshToken } = require('../config/jwt');

exports.register = async (req, res) => {
  try {
    const { username, email, password } = req.body;
    const user = await authService.register(username, email, password);
    res.status(201).json({ message: 'User registered successfully', user: { id: user.id, username: user.username, email: user.email } });
  } catch (err) {
    res.status(400).json({ error: 'Registration failed. Email or username might already exist.' });
  }
};

exports.login = async (req, res) => {
  try {
    const { identifier, password } = req.body;
    const result = await authService.login(identifier, password);

    if (result.error) return res.status(401).json({ error: result.error });

    res.json(result);
  } catch (err) {
    res.status(500).json({ error: 'Server error during login' });
  }
};

exports.googleAuth = passport.authenticate('google', { scope: ['profile', 'email'] });

exports.googleCallback = (req, res, next) => {
  passport.authenticate('google', { session: false }, async (err, user) => {
    if (err || !user) return res.redirect('/login?error=OAuthFailed');

    const result = await authService.handleGoogleCallback(user);

    // After success, usually we send token in query or generic callback route
    // But since frontend is react, redirecting to frontend URL with token in query is simple
    res.redirect(`${process.env.FRONTEND_URL}/oauth-callback?accessToken=${result.accessToken}&refreshToken=${result.refreshToken}`);
  })(req, res, next);
};

exports.refresh = async (req, res) => {
  try {
    const { refreshToken } = req.body;
    const result = await authService.refreshToken(refreshToken);

    if (result.error) return res.status(401).json({ error: result.error });

    res.json(result);
  } catch (err) {
    res.status(500).json({ error: 'Refresh token error' });
  }
};

exports.logout = async (req, res) => {
  try {
    const { refreshToken } = req.body;
    await authService.logout(refreshToken);
    res.json({ message: 'Logged out successfully' });
  } catch (err) {
    res.status(500).json({ error: 'Logout failed' });
  }
};
