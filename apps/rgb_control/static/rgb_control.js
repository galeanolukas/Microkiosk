        function updateColorPreview() {
            const r = document.getElementById('rSlider').value;
            const g = document.getElementById('gSlider').value;
            const b = document.getElementById('bSlider').value;

            document.getElementById('rValue').textContent = r;
            document.getElementById('gValue').textContent = g;
            document.getElementById('bValue').textContent = b;

            document.getElementById('colorPreview').style.backgroundColor = `rgb(${r}, ${g}, ${b})`;
        }

        function updateColor() {
            const r = document.getElementById('rSlider').value;
            const g = document.getElementById('gSlider').value;
            const b = document.getElementById('bSlider').value;

            fetch('/rgb_control/set', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({r, g, b})
            }).then(response => response.json())
              .then(data => console.log(data))
              .catch(error => console.error('Error:', error));
        }

        function setPreset(preset) {
            fetch(`/rgb_control/preset/${preset}`)
            .then(response => response.json())
            .then(data => {
                if(data.status === 'ok') {
                    const colors = {
                        'red': [255, 0, 0], 'green': [0, 255, 0], 'blue': [0, 0, 255],
                        'yellow': [255, 255, 0], 'purple': [128, 0, 128],
                        'white': [255, 255, 255], 'off': [0, 0, 0]
                    };

                    if(colors[preset]) {
                        document.getElementById('rSlider').value = colors[preset][0];
                        document.getElementById('gSlider').value = colors[preset][1];
                        document.getElementById('bSlider').value = colors[preset][2];
                        updateColorPreview();
                    }
                }
            });
        }

        document.getElementById('rSlider').addEventListener('input', updateColorPreview);
        document.getElementById('gSlider').addEventListener('input', updateColorPreview);
        document.getElementById('bSlider').addEventListener('input', updateColorPreview);

        updateColorPreview();