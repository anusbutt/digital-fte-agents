import "@testing-library/jest-dom";

if (typeof window !== "undefined") {
  class MockCanvasContext {
    clearRect = jest.fn();
    beginPath = jest.fn();
    arc = jest.fn();
    fill = jest.fn();
    moveTo = jest.fn();
    lineTo = jest.fn();
    stroke = jest.fn();
    scale = jest.fn();
    fillStyle = "";
    strokeStyle = "";
    lineWidth = 0;
  }

  Object.defineProperty(HTMLCanvasElement.prototype, "getContext", {
    value: jest.fn().mockReturnValue(new MockCanvasContext()),
  });

  Object.defineProperty(window, "matchMedia", {
    writable: true,
    value: jest.fn().mockImplementation((query) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: jest.fn(),
      removeListener: jest.fn(),
      addEventListener: jest.fn(),
      removeEventListener: jest.fn(),
      dispatchEvent: jest.fn(),
    })),
  });

  class MockResizeObserver {
    observe = jest.fn();
    unobserve = jest.fn();
    disconnect = jest.fn();
  }

  Object.defineProperty(window, "ResizeObserver", {
    writable: true,
    value: MockResizeObserver,
  });
}
