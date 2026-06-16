import { render, screen } from "@testing-library/react";
import { ParticleCanvas } from "@/components/effects/ParticleCanvas";

describe("ParticleCanvas", () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it("renders a canvas element", () => {
    render(<ParticleCanvas />);
    expect(screen.getByTestId("particle-canvas")).toBeInTheDocument();
  });

  it("cleans up animation frame on unmount", () => {
    const rafSpy = jest.spyOn(window, "requestAnimationFrame");
    const cafSpy = jest.spyOn(window, "cancelAnimationFrame");

    const { unmount } = render(<ParticleCanvas />);

    expect(rafSpy).toHaveBeenCalled();
    unmount();

    expect(cafSpy).toHaveBeenCalled();

    rafSpy.mockRestore();
    cafSpy.mockRestore();
  });
});
