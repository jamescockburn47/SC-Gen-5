import React from 'react';
import { render, screen } from '@testing-library/react';
// Mock axios to prevent ESM import issues during tests
jest.mock('axios', () => ({ get: jest.fn() }));

import App from './App';

test('renders application title', () => {
  render(<App />);
  // The title appears in both the sidebar and top bar; check at least one instance
  const titleElement = screen.getAllByText(/LexCognito/i)[0];
  expect(titleElement).toBeInTheDocument();
});
