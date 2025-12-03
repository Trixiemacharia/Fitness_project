const dashboard = document.getElementById('dashboard');
const exercisesSection = document.getElementById('exercises-section');
const exercisesList = document.getElementById('exercises-list');
const categoryTitle = document.getElementById('category-title');

const API_BASE = 'http://127.0.0.1:8000/api';

//fetch n display categories
async function loadCategories() {
    const res = await fetch('${API_BASE}/categories/');
    const categories = await res.json();
    dashboard.innerHTML = '';

    categories.forEach(cat => {
        const card = document.createElement('div');
        card.className = 'category-card';
        card.innerHTML = '<img src="${cat.image}" alt="${cat.name}"><span>${cat.name}</span>';
        card.onclick = () => showExercises(cat);
        dashboard.appendChild(card);
    });  
}

//show exercises of a category
function showExercises(category){
    categoryTitle.textContent = category.name;
    exercisesList.innerHTML = '';
    category.exercises.forEach(ex => {
        const exCard = document.createElement('div');
        exCard.className = 'exercise-card';
        //exCard.innerHTML = '<h3>${ex.name}</h3> <p>$[ex.description}</p> ${ex.demo_video ? '<video src="${ex.demo_video}" controls width="250"></video>': ''}' ;
        exercisesList.appendChild(exCard);
    });

    dashboard.style.display = 'none';
    exercisesSection.style.display = 'block';
}

//back to categories
function closeExercises(){
    exercisesSection.style.display='none';
    dashboard.style.display = 'block';
}

//initial load
loadCategories();