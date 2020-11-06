from flask import request
from flask_restx import Resource

from ..util.decorator import token_required, admin_token_required
from ..util.dto import ChannelDto
from ..service.channel_service import ChannelService
from ..service.auth_helper import Auth

import re

api = ChannelDto.api
_channel = ChannelDto.channel
_player = ChannelDto.player

@api.route('/')
class ChannelList(Resource):
    @api.doc('list_of_all_channels')
    @api.marshal_list_with(_channel, envelope='data')
    def get(self):
        """List all channels in server"""
        return ChannelService.get_all_channels()
    
    @admin_token_required
    @api.response(201, 'A new channel has successfully been added.')
    @api.doc('create a new channel (Admin)')
    @api.expect(_channel, validate=True)
    def post(self):
        """Creates a new channel"""
        data = request.json
        return ChannelService.save_new_channel(data=data)

@api.route('/<channelId>')
@api.param('channelId', 'The channel identifier')
@api.response(404, 'Channel not found.')
class Channel(Resource):
    @api.doc('get a channel')
    @api.marshal_list_with(_channel)
    def get(self, channelId):
        """get a channel given their identifier"""
        channel = ChannelService.get_a_channel(channelId)
        if not channel:
            api.abort(404)
        else:
            return channel

    @admin_token_required
    @api.response(200, 'The channel properties successfully modified.')
    @api.doc('update the channel properties')
    @api.expect(_channel, validate=False)
    def put(self, channelId):
        """update the channel\'s properties."""
        return ChannelService.update_a_channel(channelId, request.json)
        

    # def delete(self, channelId):

@api.route('/<channelId>/participants')
@api.param('channelId', 'The channel identifier')
@api.response(404, 'Channel not found')
class ParticipantsList(Resource):
    @api.doc('get a list of players participating this game.')
    @api.marshal_list_with(_player, envelope='data')
    def get(self, channelId):
        """get a list of players participating this game"""
        players = ChannelService.get_a_players_list(channelId)
        if not type(players) is list:
            api.abort(404)
        else:
            return players
    
    @api.doc('participates at this game')
    @api.expect(_player)
    def post(self, channelId):
        """Here comes a new challenger"""
        data = request.json

        # Checking name validation
        if not re.match("^[\w\d_-]*$", data['playerName']):
            api.abort(400, 'The name can only have letters, numbers, underscores and dashes.')

        data['signed'] = Auth.get_logged_in_user(request)[0]
        response = ChannelService.enter_this_channel(channelId, data)

        if not response:
            api.abort(404, 'No such channel.')
        elif response == 'exceed':
            api.abort(409, 'Exceeded maximum players number.')
        elif response == 'duplicated':
            api.abort(409, 'The name already taken by somebody in this channel.')    
        else:
            return {
                'status': 'success',
                'message': 'Successfully entered.'
            }, 201

@api.route('/<channelId>/participants/<playerId>')
@api.param('channelId', 'The channel identifier')
@api.param('playerId', 'player\'s identifier to modify')
@api.response(401, 'Only the game administrator could access this resource.')
@api.response(404, 'No such player or channel.')
class Participant(Resource):
    @admin_token_required
    @api.doc('Update players highest score')
    @api.expect(_player)
    def put(self, channelId, playerId):
        data = request.json
        response = ChannelService.update_the_score(channelId, playerId, data['highscore'])

        if not response:
            api.abort(404, 'No such channel.')
        elif response == 'noplayer':
            api.abort(404, 'No such player.')
        else:
            return {
                'status': 'success',
                'message': 'Successfully updated highscore'
            }

    @admin_token_required
    @api.doc('Delete the player from the list')
    def delete(self, channelId, playerId):
        response = ChannelService.leave_this_channel(channelId, playerId)

        if not response:
            api.abort(404, 'No such channel.')
        elif response == 'noplayer':
            api.abort(404, 'No such player.')
        else:
            return {
                'status': 'success',
                'message': 'Successfully leaved'
            }

@api.route('/<channelId>/ranking')
@api.param('channelId', 'The channel identifier')
@api.response(404, 'No such channel')
class Ranking(Resource):
    @api.marshal_list_with(_player)
    def get(self, channelId):
        ranking = ChannelService.get_channel_ranking(channelId)

        if not ranking:
            api.abort(404)
        else:
            return ranking