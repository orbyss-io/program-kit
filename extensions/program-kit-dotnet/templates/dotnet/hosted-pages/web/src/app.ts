import './styles.css';

/** Consumer-owned entry seam called by the selected HostedPages runtime. */
export async function mount(root: HTMLElement): Promise<void> {
  const heading = document.createElement('h1');
  heading.textContent = 'Application foundation';
  const status = document.createElement('p');
  status.textContent = 'Ready for consumer-specific implementation.';
  root.replaceChildren(heading, status);
}
