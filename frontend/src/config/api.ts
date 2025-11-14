/**
 * API Configuration
 * Defines the base URL for API requests
 */

// Detect the API base URL based on the current environment
const getAPIBaseURL = (): string => {
  // Check if we're running in a browser
  if (typeof window !== 'undefined') {
    // Get the protocol and host from the current window location
    const protocol = window.location.protocol;
    const hostname = window.location.hostname;
    const port = window.location.port;

    // For development, use localhost with appropriate port
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
      // Use the configured backend port
      return `${protocol}//${hostname}:3007/api`;
    }

    // For production, use the same domain
    const baseUrl = `${protocol}//${hostname}${port ? `:${port}` : ''}`;
    return `${baseUrl}/api`;
  }

  // Fallback for SSR or non-browser environments
  return '/api';
};

export const API_BASE_URL = getAPIBaseURL();
