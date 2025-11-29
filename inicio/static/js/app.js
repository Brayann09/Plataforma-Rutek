// Animación de logos en movimiento
const companies = [
  'TransAndes','Viajes Dorado','Rutas del Sol','TurisCaribe','Andes VIP',
  'MetroTour','Selva Express'
];

const makeLogo = (name) => `
  <div class="logo">
    <div class="symbol">${name.substring(0,2).toUpperCase()}</div>
    <span>${name}</span>
  </div>`;

const track = document.getElementById('marqueeTrack');
const once = companies.map(makeLogo).join('');
track.innerHTML = once + once;
