# MoodMatch Game Logic
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional
import random

@dataclass
class Player:
    id: str
    name: str
    points: int = 0
    daily_mood: Optional[str] = None
    daily_guess: Dict[str, str] = None

class MoodMatchGame:
    def __init__(self):
        self.players: Dict[str, Player] = {}
        self.emotions = [
            'happy', 'sad', 'excited', 'anxious', 'peaceful',
            'frustrated', 'grateful', 'overwhelmed', 'inspired', 'lonely'
        ]
        self.daily_reset_time = None

    def add_player(self, player_id: str, name: str) -> Player:
        """Add a new player to the game"""
        if player_id not in self.players:
            self.players[player_id] = Player(id=player_id, name=name)
        return self.players[player_id]

    def submit_mood(self, player_id: str, mood: str) -> bool:
        """Submit player's daily mood"""
        if mood not in self.emotions:
            return False
        if player_id in self.players:
            self.players[player_id].daily_mood = mood
            return True
        return False

    def submit_guess(self, guesser_id: str, target_id: str, mood: str) -> bool:
        """Submit a guess for another player's mood"""
        if mood not in self.emotions:
            return False
        if guesser_id not in self.players or target_id not in self.players:
            return False
        if guesser_id == target_id:
            return False
            
        if not self.players[guesser_id].daily_guess:
            self.players[guesser_id].daily_guess = {}
        self.players[guesser_id].daily_guess[target_id] = mood
        return True

    def calculate_points(self) -> Dict[str, int]:
        """Calculate points for all players based on correct guesses"""
        points_update = {}
        for guesser_id, player in self.players.items():
            if not player.daily_guess:
                continue
            
            points = 0
            for target_id, guessed_mood in player.daily_guess.items():
                if target_id in self.players:
                    actual_mood = self.players[target_id].daily_mood
                    if actual_mood and guessed_mood == actual_mood:
                        points += 10  # Points for correct guess
            
            self.players[guesser_id].points += points
            points_update[guesser_id] = points

        return points_update

    def get_leaderboard(self) -> List[Dict]:
        """Get sorted leaderboard of players by points"""
        sorted_players = sorted(
            self.players.values(),
            key=lambda x: x.points,
            reverse=True
        )
        return [
            {"name": p.name, "points": p.points}
            for p in sorted_players
        ]

    def daily_reset(self) -> None:
        """Reset daily moods and guesses"""
        for player in self.players.values():
            player.daily_mood = None
            player.daily_guess = {}
        self.daily_reset_time = datetime.now()

    def get_player_stats(self, player_id: str) -> Optional[Dict]:
        """Get stats for a specific player"""
        if player_id not in self.players:
            return None
            
        player = self.players[player_id]
        return {
            "name": player.name,
            "points": player.points,
            "current_mood": player.daily_mood,
            "guesses_made": len(player.daily_guess or {})
        }