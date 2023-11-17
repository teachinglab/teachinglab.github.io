
function toggle () {
  document.getElementById("TOC").classList.toggle("hide");
};

window.addEventListener('DOMContentLoaded', () => {

  const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      const id = entry.target.getAttribute('id');
      if (entry.intersectionRatio > 0) {
        document.querySelector(`[href="#${id}"]`).parentElement.classList.add('active');
      } else {
        document.querySelector(`[href="#${id}"]`).parentElement.classList.remove('active');
      }
    });
  });

  // Track all headings that have an `id` applied
  document.querySelectorAll('h1[id], h2[id], h3[id], h4[id], h5[id], h6[id]').forEach((h1, h2, h3, h4, h5, h6) => {
    observer.observe(h1, h2, h3, h4, h5, h6);
  });
  
});