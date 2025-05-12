  function toggleSidebar() {
    var bar = document.getElementById("mySidebar");
    if (bar.classList.contains("w3-hide")) {
      bar.classList.remove("w3-hide");
      document.getElementById("main").style.paddingLeft = "250px";
      document.getElementById("header").style.paddingLeft = "250px";
      document.getElementById("footer").style.marginLeft = "250px";
    } else {
      bar.classList.add("w3-hide");
      document.getElementById("main").style.paddingLeft = "0";
      document.getElementById("header").style.paddingLeft = "0";
      document.getElementById("footer").style.marginLeft = "0";
    }
  }

  function toggleAppsMenu() {
    var panel = document.getElementById("AppsPanel");
    if (panel.classList.contains("w3-hide")) {
      panel.classList.remove("w3-hide");
    } else {
      panel.classList.add("w3-hide");
    }
  }

  let currentAppToDelete = '';
  function confirmDelete(appName) {
    document.getElementById('appToDelete').textContent = appName;
    currentAppToDelete = appName;
    document.getElementById('deleteModal').style.display = 'block';
  }
  function deleteApp() {
    fetch(`/appmanager/delete?app=${encodeURIComponent(currentAppToDelete)}`, {
      method: 'POST'
    }).then(response => {
      if(response.ok) {
        window.location.reload();
      } else {
        alert('Error al eliminar');
      }
    });
    document.getElementById('deleteModal').style.display = 'none';
  }

  async function toggleFavorite(appName, btnElement) {
    const icon = btnElement.querySelector('.icon-heart');

    try {
      const response = await fetch(`/toggle_fav?app=${encodeURIComponent(appName)}`, {
        method: 'POST'
      });

      if (!response.ok) {
        throw new Error('Error del servidor');
      }

      const result = await response.json();

      if (result.status === 'success') {
        // Actualizar UI
        icon.classList.toggle('icon-red', result.is_favorite);
        icon.classList.toggle('icon-gray', !result.is_favorite);
        btnElement.title = result.is_favorite
          ? 'Quitar de favoritos'
          : 'Agregar a favoritos';
      }

    } catch (error) {
      console.error('Error al actualizar favorito:', error);
      // Opcional: Mostrar notificación al usuario
    }
  }
