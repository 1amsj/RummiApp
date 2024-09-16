class ApiSpecialSql():

    def get_event_sql(event_id):
        return """
            SELECT json_build_object(
                'id', event.id,
                'meeting_url', event.meeting_url,
                'start_at', event.start_at,
                'end_at', event.end_at,
                'observations', event.observations,
                'booking_id', event.booking_id,
                'location_id', event.location_id,
                'payer_id', event.payer_id,
                'requester_id', event.requester_id,
                'is_deleted', event.is_deleted,
                'payer_company_id', event.payer_company_id,
                'arrive_at', event.arrive_at,
                'description', event.description,
                'unique_field', event.unique_field,
                extra.key, extra.data
            )
            FROM core_backend_event event
            LEFT JOIN core_backend_extra extra on extra.parent_id = event.id
            WHERE event.id = """ + str(event_id) + """
            GROUP BY event.id, extra.key, extra.data
        """
    
    def get_extras_sql(parent_id, ):
        return """
            SELECT json_build_object(
                extra.key, extra.data
            )
            FROM core_backend_extra extra
            WHERE extra.parent_id = """ + str(parent_id)+ """
        """
        
    def get_report_sql(event_id):
        return """ 
            SELECT JSON_AGG(JSONData) FROM (
            SELECT
            ARRAY_AGG(report.status || '/' || report.id) AS reports
            FROM core_backend_report report
            WHERE report.event_id = """ + str(event_id) + """
            ) JSONData
        """


    def get_affiliates_sql(event_id):
        return """
            'affiliates', json_agg(json_build_object(
                    'id', affiliation.id,
                    'company', affiliation.company_id,
                    'recipient', json_build_object(
                        'id', recipient.id,
                        'user_id', recipient.user_id,
                        'is_deleted', recipient.is_deleted,
                        'first_name', recipientUser.first_name,
                        'last_name', recipientUser.last_name,
                        'date_of_birth', recipientUser.date_of_birth,
                        'suffix', recipientUser.suffix,
                        'title', recipientUser.title
                    ),
                    'is_deleted', affiliation.is_deleted
                ))
            SELECT JSON_AGG(JSONData) FROM (
            SELECT * FROM core_backend_event_affiliates affiliates
            LEFT JOIN core_backend_affiliation affiliation on affiliation.id = affiliates.affiliation_id
            WHERE affiliates.event_id = """ + str(event_id) + """
            ) JSONData
        """
    
    def get_recipient_sql(recipient_id):
        return """
            SELECT JSON_AGG(JSONData) FROM (
            SELECT * FROM core_backend_recipient recipient
            LEFT JOIN core_backend_user recipientUser on recipientUser.id = recipient.user_id
            WHERE recipient.id = """ + str(recipient_id) + """
        """
    
    def get_recipient_notes_sql(recipient_id):
        return """
            SELECT JSON_AGG(JSONData) FROM (
            SELECT * FROM core_backend_note noteRecipient
            WHERE noteRecipient.recipient_id = """ + str(recipient_id) + """
            ) JSONData
        """
    
    def get_user_contacts_sql(user_id):
        return """
            SELECT JSON_AGG(JSONData) FROM (
            SELECT * FROM core_backend_user_contacts userContact
            LEFT JOIN core_backend_contact contact on contact.id = userContact.contact_id
            WHERE userContact.user_id = """ + str(user_id) + """
            ) JSONData
        """
    
    def get_location_sql(location_id):
        return """
            SELECT JSON_AGG(JSONData) FROM (
            SELECT * FROM core_backend_location location
            WHERE location.id = """ + str(location_id) + """
            ) JSONData
        """
    
    def get_booking_sql(booking_id):
        return """
            SELECT JSON_AGG(JSONData) FROM (
            SELECT * FROM core_backend_booking booking
            LEFT JOIN core_backend_booking_operators bookingOperators on bookingOperators.booking_id = booking.id
            LEFT JOIN core_backend_operator operatorBooking on operatorBooking.id = bookingOperators.operator_id

            LEFT JOIN core_backend_user userOperator on userOperator.id = operatorBooking.user_id
            LEFT JOIN core_backend_user_user_permissions userPermissionsOp on userPermissionsOp.user_id = userOperator.id
            LEFT JOIN auth_permission authPermissionsOp on authPermissionsOp.id = userPermissionsOp.permission_id
            LEFT JOIN core_backend_user_groups userGroupsOp on userGroupsOp.user_id = userOperator.id
            LEFT JOIN auth_group authGroupOp on authGroupOp.id = userGroupsOp.group_id
            LEFT JOIN auth_group_permissions authGroupPermissionsOp on authGroupPermissionsOp.id = userGroupsOp.group_id
            LEFT JOIN core_backend_user_contacts userContactOperator on userContactOperator.user_id = userOperator.id
            LEFT JOIN core_backend_contact contactUsOp on contactUsOp.id = userContactOperator.contact_id
            LEFT JOIN core_backend_location locationOp on locationOp.id = userOperator.location_id
            LEFT JOIN core_backend_user_contacts userContactOp on userContactOp.user_id = userOperator.id
            LEFT JOIN core_backend_contact contactOp on contactOp.id = userContactOp.contact_id
            LEFT JOIN core_backend_booking_services bookingServices on bookingServices.booking_id = booking.id
            LEFT JOIN core_backend_service service on service.id = bookingServices.service_id
            LEFT JOIN core_backend_provider provider on provider.id = service.provider_id

            LEFT JOIN core_backend_user userProvider on userProvider.id = provider.user_id
            LEFT JOIN core_backend_user_user_permissions userPermissionsPr on userPermissionsPr.user_id = userProvider.id
            LEFT JOIN auth_permission authPermissionsPr on authPermissionsPr.id = userPermissionsPr.permission_id
            LEFT JOIN core_backend_user_groups userGroupsPr on userGroupsPr.user_id = userProvider.id
            LEFT JOIN auth_group authGroupPr on authGroupPr.id = userGroupsPr.group_id
            LEFT JOIN auth_group_permissions authGroupPermissionsPr on authGroupPermissionsPr.id = userGroupsPr.group_id
            LEFT JOIN core_backend_user_contacts userContactProvider on userContactProvider.user_id = userProvider.id
            LEFT JOIN core_backend_contact contactUsPr on contactUsPr.id = userContactProvider.contact_id
            LEFT JOIN core_backend_location locationPr on locationPr.id = userProvider.location_id
            LEFT JOIN core_backend_user_contacts userContactPr on userContactPr.user_id = userProvider.id
            LEFT JOIN core_backend_contact contactPr on contactPr.id = userContactPr.contact_id

            LEFT JOIN core_backend_booking_services bookingServicesRoot on bookingServicesRoot.booking_id = booking.id
            LEFT JOIN core_backend_serviceroot root on root.id = service.root_id
			LEFT JOIN core_backend_serviceroot_categories serviceroot on serviceroot.serviceroot_id = root.id
			LEFT JOIN core_backend_category category on category.id = serviceroot.serviceroot_id
            WHERE booking.id = """ + str(booking_id) + """
            ) JSONData
        """
    
    def get_booking_companies_sql(booking_id):
        return """
            SELECT JSON_AGG(JSONData) FROM (
            SELECT * FROM core_backend_booking_companies bookingCompanies
            LEFT JOIN core_backend_company companyAgent on companyAgent.id = bookingCompanies.company_id

            LEFT JOIN core_backend_note noteAgentCompany on noteAgentCompany.company_id = companyAgent.id

            LEFT JOIN core_backend_rate rate on rate.company_id = companyAgent.id
            LEFT JOIN core_backend_companyrelationship companyrelationship on companyrelationship.company_from_id = companyAgent.id
            LEFT JOIN core_backend_company_contacts companyContacts on companyContacts.company_id = companyAgent.id
            LEFT JOIN core_backend_contact contactCompany on contactCompany.id = companyContacts.contact_id
            LEFT JOIN core_backend_company_locations companyLocations on companyLocations.company_id = companyAgent.id
            LEFT JOIN core_backend_location locationCompany on locationCompany.id = companyLocations.location_id
            WHERE bookingCompanies.booking_id = """ + booking_id + """
            ) JSONData
        """
    
    def get_agents_sql(event_id):
        return """
            SELECT JSON_AGG(JSONData) FROM (
            SELECT * FROM core_backend_event_agents eventAgents 
            LEFT JOIN core_backend_agent agent on agent.id = eventAgents.agent_id
            LEFT JOIN core_backend_user userAgent on userAgent.id = agent.user_id
            LEFT JOIN core_backend_user_user_permissions userPermissionsAg on userPermissionsAg.user_id = userAgent.id
            LEFT JOIN auth_permission authPermissionsAg on authPermissionsAg.id = userPermissionsAg.permission_id
            LEFT JOIN core_backend_user_groups userGroupsAg on userGroupsAg.user_id = userAgent.id
            LEFT JOIN auth_group authGroupAg on authGroupAg.id = userGroupsAg.group_id
            LEFT JOIN auth_group_permissions authGroupPermissionsAg on authGroupPermissionsAg.id = userGroupsAg.group_id
            LEFT JOIN core_backend_user_contacts userContactAgent on userContactAgent.user_id = userAgent.id
            LEFT JOIN core_backend_contact contactUsAg on contactUsAg.id = userContactAgent.contact_id
            WHERE eventAgents.event_id = """+ str(event_id) +"""
            ) JSONData
        """
        
    def get_authorization_sql(event_id):
        return """
            SELECT JSON_AGG(JSONData) FROM (
            SELECT * FROM core_backend_authorization_events auth_events
            LEFT JOIN core_backend_authorization auth on auth.id = auth_events.authorization_id
            WHERE auth_events.event_id = """ + str(event_id) + """
            ) JSONData
        """
        
    def get_event_location_sql(event_id):
        return """
            SELECT JSON_AGG(JSONData) FROM (
            SELECT * FROM core_backend_location lc WHERE lc.id = """ + str(event_id)+ """
            ) JSONData
        """
        
    def get_requester_sql(requester_id):
        return """
            SELECT JSON_AGG(JSONData) FROM (
            SELECT * FROM core_backend_requester requester
			LEFT JOIN core_backend_user userRequester on userRequester.id = requester.user_id
            LEFT JOIN core_backend_user_user_permissions userPermissionsRequester on userPermissionsRequester.user_id = userRequester.id
            LEFT JOIN auth_permission authPermissionsRequester on authPermissionsRequester.id = userPermissionsRequester.permission_id
            LEFT JOIN core_backend_user_groups userGroupsRequester on userGroupsRequester.user_id = userRequester.id
            LEFT JOIN auth_group authGroupRequester on authGroupRequester.id = userGroupsRequester.group_id
            LEFT JOIN auth_group_permissions authGroupPermissionsRequester on authGroupPermissionsPayer.id = userGroupsRequester.group_id
            LEFT JOIN core_backend_location locationUsRequester on locationUsRequester.id = userRequester.location_id
            LEFT JOIN core_backend_user_contacts userContactRequester on userContactRequester.user_id = userRequester.id
            LEFT JOIN core_backend_contact contactUsRequester on contactUsRequester.id = userContactRequester.contact_id
            WHERE requester.id = """  + str(requester_id) + """
            ) JSONData
        """

    def get_payer_sql(payer_id, payer_company_id):
        return """
            SELECT JSON_AGG(JSONData) FROM (
            SELECT * FROM core_backend_payer payer
            LEFT JOIN core_backend_payer_companies payer_companies on payer_companies.id = """ + payer_company_id + """
			LEFT JOIN core_backend_company payerCompany on payerCompany.id = payer_companies.company_id
			
            LEFT JOIN core_backend_note notePayerCompany on notePayerCompany.company_id = payerCompany.id
            LEFT JOIN core_backend_rate payerRate on payerRate.company_id = payerCompany.id
            LEFT JOIN core_backend_companyrelationship companyrelationshipPayer on companyrelationshipPayer.company_from_id = payerCompany.id
            LEFT JOIN core_backend_company_contacts companyContactsPayer on companyContactsPayer.company_id = payerCompany.id
            LEFT JOIN core_backend_contact contactCompanyPayer on contactCompanyPayer.id = companyContactsPayer.contact_id
            LEFT JOIN core_backend_company_locations companyLocationsPayer on companyLocationsPayer.company_id = payerCompany.id
            LEFT JOIN core_backend_location locationCompanyPayer on locationCompanyPayer.id = companyLocationsPayer.location_id
	
			LEFT JOIN core_backend_user userPayer on userPayer.id = payer.user_id
            LEFT JOIN core_backend_user_user_permissions userPermissionsPayer on userPermissionsPayer.user_id = userPayer.id
            LEFT JOIN auth_permission authPermissionsPayer on authPermissionsPayer.id = userPermissionsPayer.permission_id
            LEFT JOIN core_backend_user_groups userGroupsPayer on userGroupsPayer.user_id = userPayer.id
            LEFT JOIN auth_group authGroupPayer on authGroupPayer.id = userGroupsPayer.group_id
            LEFT JOIN auth_group_permissions authGroupPermissionsPayer on authGroupPermissionsPayer.id = userGroupsPayer.group_id
            LEFT JOIN core_backend_location locationUsPayer on locationUsPayer.id = userPayer.location_id
            LEFT JOIN core_backend_user_contacts userContactPayer on userContactPayer.user_id = userPayer.id
            LEFT JOIN core_backend_contact contactUsPayer on contactUsPayer.id = userContactPayer.contact_id
            WHERE payer.id = """ + payer_id + """
            ) JSONData
        """
    
# Full SQL just in case we need it
# sql = """
#             SELECT JSON_AGG(t) FROM (
#             SELECT 
#                 eventData.*,
#                 ARRAY_AGG(report.status || '/' || report.id) AS reports
#             FROM core_backend_event eventData
#             -- Start Affiliates --
#             LEFT JOIN core_backend_event_affiliates affiliates on affiliates.event_id = eventData.id
#             LEFT JOIN core_backend_affiliation affiliation on affiliation.id = affiliates.affiliation_id
#             LEFT JOIN core_backend_recipient recipient on recipient.id = affiliation.recipient_id
#             LEFT JOIN core_backend_user userRecipient on userRecipient.id = recipient.user_id
#             LEFT JOIN core_backend_user_user_permissions userPermissions on userPermissions.user_id = userRecipient.id
#             LEFT JOIN auth_permission authPermissions on authPermissions.id = userPermissions.permission_id
#             LEFT JOIN core_backend_user_groups userGroups on userGroups.user_id = userRecipient.id
#             LEFT JOIN auth_group authGroup on authGroup.id = userGroups.group_id
#             LEFT JOIN auth_group_permissions authGroupPermissions on authGroupPermissions.id = userGroups.group_id
#             LEFT JOIN core_backend_location locationUs on locationUs.id = userRecipient.location_id
#             LEFT JOIN core_backend_user_contacts userContact on userContact.user_id = userRecipient.id
#             LEFT JOIN core_backend_contact contactUs on contactUs.id = userContact.contact_id
#             -- End Affiliates --

#             -- Start Agents --
#             LEFT JOIN core_backend_event_agents eventAgents on eventAgents.event_id = eventData.id
#             LEFT JOIN core_backend_agent agent on agent.id = eventAgents.agent_id
#             LEFT JOIN core_backend_user userAgent on userAgent.id = agent.user_id
#             LEFT JOIN core_backend_user_user_permissions userPermissionsAg on userPermissionsAg.user_id = userAgent.id
#             LEFT JOIN auth_permission authPermissionsAg on authPermissionsAg.id = userPermissionsAg.permission_id
#             LEFT JOIN core_backend_user_groups userGroupsAg on userGroupsAg.user_id = userAgent.id
#             LEFT JOIN auth_group authGroupAg on authGroupAg.id = userGroupsAg.group_id
#             LEFT JOIN auth_group_permissions authGroupPermissionsAg on authGroupPermissionsAg.id = userGroupsAg.group_id
#             LEFT JOIN core_backend_user_contacts userContactAgent on userContactAgent.user_id = userAgent.id
#             LEFT JOIN core_backend_contact contactUsAg on contactUsAg.id = userContactAgent.contact_id
#             -- End Agents --

#             -- Start Authorization --
#             LEFT JOIN core_backend_authorization_events auth_events on auth_events.event_id = eventData.id
#             LEFT JOIN core_backend_authorization auth on auth.id = auth_events.authorization_id
#             -- End Authorization --

#             -- Start Booking --
#             LEFT JOIN core_backend_booking booking on booking_id = booking.id
#             LEFT JOIN core_backend_booking_operators bookingOperators on bookingOperators.booking_id = booking.id
#             LEFT JOIN core_backend_operator operatorBooking on operatorBooking.id = bookingOperators.operator_id

#             LEFT JOIN core_backend_user userOperator on userOperator.id = operatorBooking.user_id
#             LEFT JOIN core_backend_user_user_permissions userPermissionsOp on userPermissionsOp.user_id = userOperator.id
#             LEFT JOIN auth_permission authPermissionsOp on authPermissionsOp.id = userPermissionsOp.permission_id
#             LEFT JOIN core_backend_user_groups userGroupsOp on userGroupsOp.user_id = userOperator.id
#             LEFT JOIN auth_group authGroupOp on authGroupOp.id = userGroupsOp.group_id
#             LEFT JOIN auth_group_permissions authGroupPermissionsOp on authGroupPermissionsOp.id = userGroupsOp.group_id
#             LEFT JOIN core_backend_user_contacts userContactOperator on userContactOperator.user_id = userOperator.id
#             LEFT JOIN core_backend_contact contactUsOp on contactUsOp.id = userContactOperator.contact_id
#             LEFT JOIN core_backend_location locationOp on locationOp.id = userOperator.location_id
#             LEFT JOIN core_backend_user_contacts userContactOp on userContactOp.user_id = userOperator.id
#             LEFT JOIN core_backend_contact contactOp on contactOp.id = userContactOp.contact_id
#             LEFT JOIN core_backend_booking_services bookingServices on bookingServices.booking_id = booking.id
#             LEFT JOIN core_backend_service service on service.id = bookingServices.service_id
#             LEFT JOIN core_backend_provider provider on provider.id = service.provider_id

#             LEFT JOIN core_backend_user userProvider on userProvider.id = provider.user_id
#             LEFT JOIN core_backend_user_user_permissions userPermissionsPr on userPermissionsPr.user_id = userProvider.id
#             LEFT JOIN auth_permission authPermissionsPr on authPermissionsPr.id = userPermissionsPr.permission_id
#             LEFT JOIN core_backend_user_groups userGroupsPr on userGroupsPr.user_id = userProvider.id
#             LEFT JOIN auth_group authGroupPr on authGroupPr.id = userGroupsPr.group_id
#             LEFT JOIN auth_group_permissions authGroupPermissionsPr on authGroupPermissionsPr.id = userGroupsPr.group_id
#             LEFT JOIN core_backend_user_contacts userContactProvider on userContactProvider.user_id = userProvider.id
#             LEFT JOIN core_backend_contact contactUsPr on contactUsPr.id = userContactProvider.contact_id
#             LEFT JOIN core_backend_location locationPr on locationPr.id = userProvider.location_id
#             LEFT JOIN core_backend_user_contacts userContactPr on userContactPr.user_id = userProvider.id
#             LEFT JOIN core_backend_contact contactPr on contactPr.id = userContactPr.contact_id

#             LEFT JOIN core_backend_booking_services bookingServicesRoot on bookingServicesRoot.booking_id = booking.id
#             LEFT JOIN core_backend_serviceroot root on root.id = service.root_id
# 			LEFT JOIN core_backend_serviceroot_categories serviceroot on serviceroot.serviceroot_id = root.id
# 			LEFT JOIN core_backend_category category on category.id = serviceroot.serviceroot_id

#             LEFT JOIN core_backend_booking_companies bookingCompanies on bookingCompanies.booking_id = booking.id
#             LEFT JOIN core_backend_company companyAgent on companyAgent.id = bookingCompanies.company_id
#             LEFT JOIN core_backend_note noteAgentCompany on noteAgentCompany.company_id = companyAgent.id
#             LEFT JOIN core_backend_rate rate on rate.company_id = companyAgent.id
#             LEFT JOIN core_backend_companyrelationship companyrelationship on companyrelationship.company_from_id = companyAgent.id
#             LEFT JOIN core_backend_company_contacts companyContacts on companyContacts.company_id = companyAgent.id
#             LEFT JOIN core_backend_contact contactCompany on contactCompany.id = companyContacts.contact_id
#             LEFT JOIN core_backend_company_locations companyLocations on companyLocations.company_id = companyAgent.id
#             LEFT JOIN core_backend_location locationCompany on locationCompany.id = companyLocations.location_id
#             -- End Booking --

#             LEFT JOIN core_backend_location lc on eventData.location_id = lc.id
# 			-- Start Payer --
#             LEFT JOIN core_backend_payer payer on eventData.payer_id = payer.id
#             LEFT JOIN core_backend_payer_companies payer_companies on payer_companies.id = eventData.payer_company_id
# 			LEFT JOIN core_backend_company payerCompany on payerCompany.id = payer_companies.company_id
			
#             LEFT JOIN core_backend_note notePayerCompany on notePayerCompany.company_id = payerCompany.id
#             LEFT JOIN core_backend_rate payerRate on payerRate.company_id = payerCompany.id
#             LEFT JOIN core_backend_companyrelationship companyrelationshipPayer on companyrelationshipPayer.company_from_id = payerCompany.id
#             LEFT JOIN core_backend_company_contacts companyContactsPayer on companyContactsPayer.company_id = payerCompany.id
#             LEFT JOIN core_backend_contact contactCompanyPayer on contactCompanyPayer.id = companyContactsPayer.contact_id
#             LEFT JOIN core_backend_company_locations companyLocationsPayer on companyLocationsPayer.company_id = payerCompany.id
#             LEFT JOIN core_backend_location locationCompanyPayer on locationCompanyPayer.id = companyLocationsPayer.location_id
	
# 			LEFT JOIN core_backend_user userPayer on userPayer.id = payer.user_id
#             LEFT JOIN core_backend_user_user_permissions userPermissionsPayer on userPermissionsPayer.user_id = userPayer.id
#             LEFT JOIN auth_permission authPermissionsPayer on authPermissionsPayer.id = userPermissionsPayer.permission_id
#             LEFT JOIN core_backend_user_groups userGroupsPayer on userGroupsPayer.user_id = userPayer.id
#             LEFT JOIN auth_group authGroupPayer on authGroupPayer.id = userGroupsPayer.group_id
#             LEFT JOIN auth_group_permissions authGroupPermissionsPayer on authGroupPermissionsPayer.id = userGroupsPayer.group_id
#             LEFT JOIN core_backend_location locationUsPayer on locationUsPayer.id = userPayer.location_id
#             LEFT JOIN core_backend_user_contacts userContactPayer on userContactPayer.user_id = userPayer.id
#             LEFT JOIN core_backend_contact contactUsPayer on contactUsPayer.id = userContactPayer.contact_id
# 			-- End Payer --
			
# 			-- Start Requester --
#             LEFT JOIN core_backend_requester requester on requester_id = requester.id
# 			LEFT JOIN core_backend_user userRequester on userRequester.id = requester.user_id
#             LEFT JOIN core_backend_user_user_permissions userPermissionsRequester on userPermissionsRequester.user_id = userRequester.id
#             LEFT JOIN auth_permission authPermissionsRequester on authPermissionsRequester.id = userPermissionsRequester.permission_id
#             LEFT JOIN core_backend_user_groups userGroupsRequester on userGroupsRequester.user_id = userRequester.id
#             LEFT JOIN auth_group authGroupRequester on authGroupRequester.id = userGroupsRequester.group_id
#             LEFT JOIN auth_group_permissions authGroupPermissionsRequester on authGroupPermissionsPayer.id = userGroupsRequester.group_id
#             LEFT JOIN core_backend_location locationUsRequester on locationUsRequester.id = userRequester.location_id
#             LEFT JOIN core_backend_user_contacts userContactRequester on userContactRequester.user_id = userRequester.id
#             LEFT JOIN core_backend_contact contactUsRequester on contactUsRequester.id = userContactRequester.contact_id
# 			-- End Requester --
	
# 			-- Start Report --
#             LEFT JOIN core_backend_report report on report.event_id = eventData.id
# 			-- End Report --

#             where eventData.id = 7512
#             GROUP BY eventData.id
#             ) t
#             """

    @staticmethod
    def get_company_sql_where_clause(id, name, type, send_method, on_hold, limit, offset):
        params = []
        limit_statement = ''
        where_conditions = 'company.is_deleted = FALSE'

        if id is not None:
            where_conditions += ' AND company.id = %s'
            params.append(id)

        if name is not None:
            where_conditions += ' AND company.name ILIKE %s'
            params.append(name)

        if type is not None:
            where_conditions += ' AND company.type = %s'
            params.append(type)

        if send_method is not None:
            where_conditions += ' AND company.send_method = %s'
            params.append(send_method)

        if on_hold is not None:
            where_conditions += ' AND company.on_hold = %s'
            params.append(on_hold)

        if limit is not None and limit > 0 and offset is not None and offset >= 0:
            limit_statement = 'LIMIT %s OFFSET %s'
            params.append(limit)
            params.append(offset)

        return params, where_conditions, limit_statement

    @staticmethod
    def get_company_sql(cursor, id, name, type, send_method, on_hold, limit, offset):
        params, where_conditions, limit_statement = ApiSpecialSql.get_company_sql_where_clause(id, name, type, send_method, on_hold, limit, offset)

        query = """
            SELECT json_agg(row_to_json(_query_result)) AS result FROM (
                SELECT
                    company.id,
                    COALESCE((
                        SELECT
                            json_agg(row_to_json(_contacts))
                        FROM "core_backend_company_contacts" _company_contacts
                            INNER JOIN "core_backend_contact" _contacts
                                ON _contacts.id = _company_contacts.contact_id
                        WHERE _company_contacts.company_id = company.id AND _contacts.is_deleted=FALSE
                    ), '[]'::JSON) AS contacts,
                    COALESCE((
                        SELECT
                            json_agg(row_to_json(_locations))
                        FROM "core_backend_company_locations" _company_locations
                            INNER JOIN "core_backend_location" _locations
                                ON _locations.id = _company_locations.location_id
                        WHERE _company_locations.company_id = company.id AND _locations.is_deleted=FALSE
                    ), '[]'::JSON) AS locations,
                    COALESCE((
                        SELECT
                            json_agg(
                                json_build_object(
                                'id', _company_note.id,
                                'created_by', _company_note.created_by_id,
                                'created_by_first_name', _note_created_by.first_name,
                                'created_by_last_name', _note_created_by.last_name,
                                'text', _company_note.text,
                                'is_deleted', _company_note.is_deleted,
                                'created_at', _company_note.created_at,
                                'last_updated_at', _company_note.last_updated_at,
                                'booking', _company_note.booking_id,
                                'company', _company_note.company_id,
                                'notification', _company_note.notification_id,
                                'payer', _company_note.payer_id,
                                'provider', _company_note.provider_id,
                                'recipient', _company_note.recipient_id
                                )
                            )
                        FROM "core_backend_note" _company_note
                            INNER JOIN "core_backend_user" _note_created_by
                                ON _company_note.created_by_id = _note_created_by.id
                        WHERE _company_note.company_id = company.id AND _company_note.is_deleted=FALSE
                    ), '[]'::JSON) AS notes,
                    (
                        SELECT
                            json_build_object(
                            'id', _company.id,
                            'contacts', COALESCE((
                                SELECT
                                    json_agg(row_to_json(_contacts))
                                FROM "core_backend_company_contacts" _company_contacts
                                    INNER JOIN "core_backend_contact" _contacts
                                        ON _contacts.id = _company_contacts.contact_id
                                WHERE _company_contacts.company_id = _company.id AND _contacts.is_deleted=FALSE
                            ), '[]'::JSON),
                            'locations', COALESCE((
                                SELECT
                                    json_agg(row_to_json(_locations))
                                FROM "core_backend_company_locations" _company_locations
                                    INNER JOIN "core_backend_location" _locations
                                        ON _locations.id = _company_locations.location_id
                                WHERE _company_locations.company_id = _company.id AND _locations.is_deleted=FALSE
                            ), '[]'::JSON),
                            'notes',     COALESCE((
                                SELECT
                                    json_agg(
                                        json_build_object(
                                        'id', _company_note.id,
                                        'created_by', _company_note.created_by_id,
                                        'created_by_first_name', _note_created_by.first_name,
                                        'created_by_last_name', _note_created_by.last_name,
                                        'text', _company_note.text,
                                        'is_deleted', _company_note.is_deleted,
                                        'created_at', _company_note.created_at,
                                        'last_updated_at', _company_note.last_updated_at,
                                        'booking', _company_note.booking_id,
                                        'company', _company_note.company_id,
                                        'notification', _company_note.notification_id,
                                        'payer', _company_note.payer_id,
                                        'provider', _company_note.provider_id,
                                        'recipient', _company_note.recipient_id
                                        )
                                    )
                                FROM "core_backend_note" _company_note
                                    INNER JOIN "core_backend_user" _note_created_by
                                        ON _company_note.created_by_id = _note_created_by.id
                                WHERE _company_note.company_id = _company.id AND _company_note.is_deleted=FALSE
                            ), '[]'::JSON),
                            'parent_company_id', _company.parent_company_id,
                            'is_deleted', _company.is_deleted,
                            'name', _company.name,
                            'type', _company.type,
                            'send_method', _company.send_method,
                            'on_hold', _company.on_hold,
                            'aliases', _company.aliases
                            )
                        FROM "core_backend_company" _company
                        WHERE _company.id = company.parent_company_id
                    ) AS parent_company,
                    COALESCE((
                        SELECT
                            json_agg(row_to_json(_company_rate))
                        FROM "core_backend_rate" _company_rate
                        WHERE _company_rate.company_id = company.id AND _company_rate.is_deleted=FALSE
                    ), '[]'::JSON) AS rates,
                    COALESCE((
                        SELECT
                            json_agg(row_to_json(_company_relationship))
                        FROM "core_backend_companyrelationship" _company_relationship
                        WHERE _company_relationship.company_from_id = company.id AND _company_relationship.is_deleted=FALSE
                    ), '[]'::JSON) AS company_relationships_from,
                    company.is_deleted,
                    company.name,
                    company.type,
                    company.send_method,
                    company.on_hold,
                    company.aliases
                FROM "core_backend_company" company
                WHERE %s
                ORDER BY company.name, company.id
                %s
            ) _query_result
        """ % (where_conditions, limit_statement)

        cursor.execute(query, params)
        result = cursor.fetchone()
        if len(result) == 1:
            return result[0]

        return []

    @staticmethod
    def get_company_with_roles_sql(cursor, id, name, type, send_method, on_hold, limit, offset):
        params, where_conditions, limit_statement = ApiSpecialSql.get_company_sql_where_clause(id, name, type, send_method, on_hold, limit, offset)

        query = """
            SELECT json_agg(row_to_json(_query_result)) AS result FROM (
                SELECT
                    company.id,
                    COALESCE((
                        SELECT
                            json_agg(row_to_json(_contacts))
                        FROM "core_backend_company_contacts" _company_contacts
                            INNER JOIN "core_backend_contact" _contacts
                                ON _contacts.id = _company_contacts.contact_id
                        WHERE _company_contacts.company_id = company.id AND _contacts.is_deleted=FALSE
                    ), '[]'::JSON) AS contacts,
                    COALESCE((
                        SELECT
                            json_agg(row_to_json(_locations))
                        FROM "core_backend_company_locations" _company_locations
                            INNER JOIN "core_backend_location" _locations
                                ON _locations.id = _company_locations.location_id
                        WHERE _company_locations.company_id = company.id AND _locations.is_deleted=FALSE
                    ), '[]'::JSON) AS locations,
                    COALESCE((
                        SELECT
                            json_agg(
                                json_build_object(
                                'id', _company_note.id,
                                'created_by', _company_note.created_by_id,
                                'created_by_first_name', _note_created_by.first_name,
                                'created_by_last_name', _note_created_by.last_name,
                                'text', _company_note.text,
                                'is_deleted', _company_note.is_deleted,
                                'created_at', _company_note.created_at,
                                'last_updated_at', _company_note.last_updated_at,
                                'booking', _company_note.booking_id,
                                'company', _company_note.company_id,
                                'notification', _company_note.notification_id,
                                'payer', _company_note.payer_id,
                                'provider', _company_note.provider_id,
                                'recipient', _company_note.recipient_id
                                )
                            )
                        FROM "core_backend_note" _company_note
                            INNER JOIN "core_backend_user" _note_created_by
                                ON _company_note.created_by_id = _note_created_by.id
                        WHERE _company_note.company_id = company.id AND _company_note.is_deleted=FALSE
                    ), '[]'::JSON) AS notes,
                    COALESCE((
                        SELECT JSON_AGG(t) FROM ( 
                        SELECT payer.*, COALESCE(id IS NULL, false) AS is_payer, payer_lateral.* FROM core_backend_payer payer,
                        LATERAL (
                            SELECT username, email, first_name, last_name, national_id, ssn, date_of_birth, title, suffix,
                            user_contacts_lateral.*, contacts_lateral.*, company_lateral.*, notes_lateral.*, location_lateral.*, payer_companies_lateral.* FROM core_backend_user,
                            LATERAL (
                                SELECT JSON_AGG(t) -> 0 as user_contacts_ids FROM (
                                SELECT contact_id FROM core_backend_user_contacts WHERE core_backend_user_contacts.user_id = core_backend_user.id
                                ) t
                            ) AS user_contacts_lateral,
                            LATERAL (
                                SELECT JSON_AGG(t) as contacts FROM (
                                SELECT * FROM core_backend_contact WHERE core_backend_contact.id = (user_contacts_lateral.user_contacts_ids ->> 'contact_id')::integer
                                ) t
                            ) As contacts_lateral,  
                            LATERAL (
                                SELECT payer_id AS payer_id, company_id as company_id FROM core_backend_payer_companies WHERE payer_id = payer.id
                            ) AS payer_companies_lateral,
                            LATERAL (
                                SELECT JSON_AGG(t) as companies FROM (
                                SELECT * FROM core_backend_company WHERE core_backend_company.id = company_id
                                ) t
                            ) As company_lateral,
                            LATERAL (
                                SELECT JSON_AGG(t) as notes FROM (
                                SELECT * FROM core_backend_note WHERE core_backend_note.payer_id = payer_id
                                ) t
                            ) As notes_lateral,
                            LATERAL (
                                SELECT JSON_AGG(t) as location FROM (
                                SELECT * FROM core_backend_location WHERE core_backend_location.id = core_backend_user.location_id
                                ) t
                            ) As location_lateral
                            WHERE core_backend_user.id = payer.user_id
                        ) AS payer_lateral
                        WHERE company_id = company.id
                        ) t
                    ), '[]'::JSON) AS payer,
                    COALESCE((
                        SELECT JSON_AGG(t) as agents FROM (
                            SELECT ARRAY[core_backend_agent_companies.agent_id] as agents_id, 
                            ARRAY[core_backend_agent_companies.id] as companies, 
                            agent_lateral.*, user_lateral.*, user_contacts_lateral.*,
                            location_lateral.*, contacts_lateral.*, requester_lateral.*, payer_lateral.*
                            FROM core_backend_agent_companies,
                            LATERAL (
                                SELECT agent_id as id, role, is_deleted, user_id AS userId, user_id FROM core_backend_agent WHERE id = core_backend_agent_companies.agent_id
                            ) as agent_lateral,
                            LATERAL (
                                SELECT username, email, first_name, last_name, national_id, ssn, date_of_birth, title, suffix, location_id FROM core_backend_user
                                WHERE core_backend_user.id = userId
                            ) AS user_lateral,
                            LATERAL (
                                SELECT JSON_AGG(t) -> 0 as user_contacts_ids FROM (
                                SELECT contact_id FROM core_backend_user_contacts WHERE core_backend_user_contacts.user_id = userId
                                ) t
                            ) AS user_contacts_lateral,
                            LATERAL (
                                SELECT JSON_AGG(t) as contacts FROM (
                                SELECT * FROM core_backend_contact WHERE core_backend_contact.id = (user_contacts_lateral.user_contacts_ids ->> 'contact_id')::integer
                                ) t
                            ) As contacts_lateral,
                            LATERAL (
                                SELECT JSON_AGG(t) as location FROM (
                                SELECT * FROM core_backend_location WHERE core_backend_location.id = location_id
                                ) t
                            ) As location_lateral,
                            LATERAL (
                                SELECT id as requester_id, COALESCE(id IS NOT NULL, true) as is_requester FROM core_backend_requester WHERE core_backend_requester.user_id = userId
                            ) AS requester_lateral,
                            LATERAL (
                                SELECT id as payer_id, COALESCE(id IS NOT NULL, true) as is_payer FROM core_backend_payer WHERE core_backend_payer.user_id = userId
                            ) AS payer_lateral
                            WHERE core_backend_agent_companies.company_id = company.id
                        ) t
                    ), '[]'::JSON) AS agents,
                    (
                        SELECT
                            json_build_object(
                            'id', _company.id,
                            'contacts', COALESCE((
                                SELECT
                                    json_agg(row_to_json(_contacts))
                                FROM "core_backend_company_contacts" _company_contacts
                                    INNER JOIN "core_backend_contact" _contacts
                                        ON _contacts.id = _company_contacts.contact_id
                                WHERE _company_contacts.company_id = _company.id AND _contacts.is_deleted=FALSE
                            ), '[]'::JSON),
                            'locations', COALESCE((
                                SELECT
                                    json_agg(row_to_json(_locations))
                                FROM "core_backend_company_locations" _company_locations
                                    INNER JOIN "core_backend_location" _locations
                                        ON _locations.id = _company_locations.location_id
                                WHERE _company_locations.company_id = _company.id AND _locations.is_deleted=FALSE
                            ), '[]'::JSON),
                            'notes',     COALESCE((
                                SELECT
                                    json_agg(
                                        json_build_object(
                                        'id', _company_note.id,
                                        'created_by', _company_note.created_by_id,
                                        'created_by_first_name', _note_created_by.first_name,
                                        'created_by_last_name', _note_created_by.last_name,
                                        'text', _company_note.text,
                                        'is_deleted', _company_note.is_deleted,
                                        'created_at', _company_note.created_at,
                                        'last_updated_at', _company_note.last_updated_at,
                                        'booking', _company_note.booking_id,
                                        'company', _company_note.company_id,
                                        'notification', _company_note.notification_id,
                                        'payer', _company_note.payer_id,
                                        'provider', _company_note.provider_id,
                                        'recipient', _company_note.recipient_id
                                        )
                                    )
                                FROM "core_backend_note" _company_note
                                    INNER JOIN "core_backend_user" _note_created_by
                                        ON _company_note.created_by_id = _note_created_by.id
                                WHERE _company_note.company_id = _company.id AND _company_note.is_deleted=FALSE
                            ), '[]'::JSON),
                            'parent_company_id', _company.parent_company_id,
                            'is_deleted', _company.is_deleted,
                            'name', _company.name,
                            'type', _company.type,
                            'send_method', _company.send_method,
                            'on_hold', _company.on_hold,
                            'aliases', _company.aliases
                            )
                        FROM "core_backend_company" _company
                        WHERE _company.id = company.parent_company_id
                    ) AS parent_company,
                    COALESCE((
                        SELECT
                            json_agg(row_to_json(_company_rate))
                        FROM "core_backend_rate" _company_rate
                        WHERE _company_rate.company_id = company.id AND _company_rate.is_deleted=FALSE
                    ), '[]'::JSON) AS rates,
                    COALESCE((
                        SELECT
                            json_agg(row_to_json(_company_relationship))
                        FROM "core_backend_companyrelationship" _company_relationship
                        WHERE _company_relationship.company_from_id = company.id AND _company_relationship.is_deleted=FALSE
                    ), '[]'::JSON) AS company_relationships_from,
                    company.is_deleted,
                    company.name,
                    company.type,
                    company.send_method,
                    company.on_hold,
                    company.aliases
                FROM "core_backend_company" company
                WHERE %s
                ORDER BY company.name, company.id
                %s
            ) _query_result
        """ % (where_conditions, limit_statement)

        cursor.execute(query, params)
        result = cursor.fetchone()
        if len(result) == 1:
            return result[0]

        return []

    @staticmethod
    def get_company_count_sql(cursor, id, name, type, send_method, on_hold):
        params, where_conditions, _ = ApiSpecialSql.get_company_sql_where_clause(id, name, type, send_method, on_hold, None, None)

        query = """
            SELECT
               COUNT(*)
            FROM "core_backend_company" company
            WHERE %s
        """ % where_conditions

        cursor.execute(query, params)
        result = cursor.fetchone()
        if len(result) == 1:
            return result[0]

        return 0