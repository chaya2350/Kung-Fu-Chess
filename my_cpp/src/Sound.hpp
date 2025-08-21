#pragma once
#include <SDL.h>
#include <SDL_mixer.h>
#include <string>
#include <iostream>

class Sound {
public:
    Mix_Chunk* _sound;

    // בנאי - אתחול SDL ו-SDL_mixer
    Sound() : _sound(nullptr) {
        if (SDL_Init(SDL_INIT_AUDIO) < 0) {
            std::cout << "error in SDL_Init: " << SDL_GetError() << std::endl;
        }
        if (Mix_OpenAudio(22050, MIX_DEFAULT_FORMAT, 2, 4096) < 0) {
            std::cout << "error in Mix_OpenAudio: " << Mix_GetError() << std::endl;
        }
    }

    // דסטרקטור - שחרור משאבים
    ~Sound() {
        if (_sound) {
            Mix_FreeChunk(_sound);
        }
        Mix_CloseAudio();
        if (SDL_WasInit(SDL_INIT_AUDIO)) {
            SDL_Quit();
        }
    }

    // ניגון קובץ קול
    void play(const std::string& sound_file) {
        if (_sound) {
            Mix_FreeChunk(_sound);
            _sound = nullptr;
        }
        _sound = Mix_LoadWAV(sound_file.c_str());
        if (!_sound) {
            std::cout << "[ERROR] Failed to load sound file: " << sound_file << std::endl;
            std::cout << "[ERROR] Mix_LoadWAV: " << Mix_GetError() << std::endl;
            return;
        }
        Mix_PlayChannel(-1, _sound, 0);
    }

    // עצירת קול
    void stop() {
        if (_sound) {
            Mix_HaltChannel(-1);
        }
    }
};
