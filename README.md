# Imagen Fork - DameMano

Fork du plugin [sanjay3290/ai-skills/imagen](https://github.com/sanjay3290/ai-skills) pour le projet DameMano.

## Modifications par rapport à l'original

- **Force l'extension `.jpg`** - L'API Gemini retourne toujours du JPEG, le script corrige automatiquement l'extension
- Simplification pour macOS/Linux uniquement
- Instructions custom pour DameMano (voir SKILL.md)

## Usage

```bash
python3 tools/imagen-fork/scripts/generate_image.py "prompt" "output.jpg"
```

Si vous passez `.png`, le script le convertira automatiquement en `.jpg`.

## Configuration

```bash
export GEMINI_API_KEY="your-key"

# Persister dans ~/.zshrc
echo 'export GEMINI_API_KEY="your-key"' >> ~/.zshrc
```

Obtenir une clé gratuite: https://aistudio.google.com/

## Tailles d'image

| Size | Resolution | Usage |
|------|------------|-------|
| `512` | 512x512 | Icônes, thumbnails |
| `1K` | 1024x1024 | Usage général (défaut) |
| `2K` | 2048x2048 | Haute résolution |

```bash
# Avec taille spécifique
python3 scripts/generate_image.py --size 2K "prompt" "output.jpg"

# Variables d'environnement
export IMAGE_SIZE="2K"  # Taille par défaut
export GEMINI_MODEL="gemini-3-pro-image-preview"  # Modèle
```

## Troubleshooting

| Erreur | Cause | Solution |
|--------|-------|----------|
| 400 | Prompt invalide | Vérifier les caractères spéciaux |
| 403 | Clé API invalide | Vérifier GEMINI_API_KEY |
| 429 | Rate limit | Attendre et réessayer |

## Licence

Apache-2.0 (héritée du projet original)
