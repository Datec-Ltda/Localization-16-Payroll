import logging

from odoo import api, models

from odoo.addons.hr_employee_firstname.models.hr_employee import UPDATE_PARTNER_FIELDS

_logger = logging.getLogger(__name__)

UPDATE_PARTNER_FIELDS += ["lastname2"]


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    @api.model
    def _get_name_lastnames(self, treatment, lastname, firstname, firstname2, lastname2=None, married_name=None):
        order = self._get_names_order()
        names = list()
        if order == "first_last":
            if treatment:
                names.append(treatment)
            if firstname:
                names.append(firstname)
            if firstname2:
                names.append(firstname2)
            if lastname:
                names.append(lastname)
            if lastname2:
                names.append(lastname2)
            if married_name:
                names.append(married_name)
        else:
            if treatment:
                names.append(treatment)
            if lastname:
                names.append(lastname)
            if lastname2:
                names.append(lastname2)
            if names and firstname and order == "last_first_comma":
                names[-1] = names[-1] + ","
            if firstname:
                names.append(firstname)
            if firstname2:
                names.append(firstname2)
            if married_name:
                names.append(married_name)
        return " ".join(names)

    def _prepare_vals_on_create_firstname_lastname(self, vals):
        values = vals.copy()
        res = super(
            HrEmployee, self)._prepare_vals_on_create_firstname_lastname(values)
        if any([field in vals for field in ("treatment", "firstname", "lastname", "firstname2", "lastname2", "married_name")]):
            vals["name"] = self._get_name_lastnames(
                vals.get("treatment"), vals.get(
                    "lastname"), vals.get("firstname"),
                vals.get("firstname2"), vals.get("lastname2"), vals.get("married_name"))
        elif vals.get("name"):
            name_splitted = self.split_name(vals["name"])
            keys = vals.keys()
            if 'treatment' in keys:
                vals["treatment"] = name_splitted["treatment"]
            if 'lastname' in keys:
                vals["lastname"] = name_splitted["lastname"]
            if 'firstname' in keys:
                vals["firstname"] = name_splitted["firstname"]
            if 'firstname2' in keys:
                vals["firstname2"] = name_splitted["firstname2"]
            if 'lastname2' in keys:
                vals["lastname2"] = name_splitted["lastname2"]
            if 'married_name' in keys:
                vals["married_name"] = name_splitted["married_name"]
        return res

    def _prepare_vals_on_write_firstname_lastname(self, vals):
        values = vals.copy()
        res = super(
            HrEmployee, self)._prepare_vals_on_write_firstname_lastname(values)
        if any([field in vals for field in ("treatment", "firstname", "lastname", "firstname2", "lastname2", "married_name")]):
            if "treatment" in vals:
                treatment = vals["treatment"]
            else:
                treatment = self.treatment
            if "lastname" in vals:
                lastname = vals["lastname"]
            else:
                lastname = self.lastname
            if "firstname" in vals:
                firstname = vals["firstname"]
            else:
                firstname = self.firstname
            if "firstname2" in vals:
                firstname2 = vals["firstname2"]
            else:
                firstname2 = self.firstname2
            if "lastname2" in vals:
                lastname2 = vals["lastname2"]
            else:
                lastname2 = self.lastname2
            if "married_name" in vals:
                married_name = vals["married_name"]
            else:
                married_name = self.married_name
            vals["name"] = self._get_name_lastnames(
                treatment, lastname, firstname, firstname2, lastname2, married_name)
        elif vals.get("name"):
            name_splitted = self.split_name(vals["name"])
            keys = vals.keys()
            if 'treatment' in keys:
                vals["treatment"] = name_splitted["treatment"]
            if 'lastname' in keys:
                vals["lastname"] = name_splitted["lastname"]
            if 'firstname' in keys:
                vals["firstname"] = name_splitted["firstname"]
            if 'firstname2' in keys:
                vals["firstname2"] = name_splitted["firstname2"]
            if 'lastname2' in keys:
                vals["lastname2"] = name_splitted["lastname2"]
            if 'married_name' in keys:
                vals["married_name"] = name_splitted["married_name"]
        return res

    def _update_partner_firstname(self):
        for employee in self:
            partners = employee.mapped("user_id.partner_id")
            partners |= employee.mapped("address_home_id")
            partners.write(
                {
                    "firstname": employee.firstname,
                    "firstname2": employee.firstname2,
                    "lastname": employee.lastname,
                    "lastname2": employee.lastname2,
                }
            )

    @api.model
    def _get_inverse_name(self, name):
        """Compute the inverted name."""
        result = {
            "firstname": False,
            "firstname2": False,
            "lastname": name or False,
            "lastname2": False,
        }

        if not name:
            return result

        order = self._get_names_order()
        result.update(super(HrEmployee, self)._get_inverse_name(name))

        if order in ("first_last", "last_first_comma"):
            parts = self._split_part("lastname", result)
            if parts:
                result.update(
                    {"lastname": parts[0], "lastname2": " ".join(parts[1:])})
        else:
            parts = self._split_part("firstname", result)
            if parts:
                result.update(
                    {"firstname": parts[-1], "lastname2": " ".join(parts[:-1])}
                )
        return result

    def _split_part(self, name_part, name_split):
        """Split a given part of a name.

        :param name_split: The parts of the name
        :type dict

        :param name_part: The part to split
        :type str
        """
        name = name_split.get(name_part, False)
        parts = name.split(" ", 1) if name else []
        if not name or len(parts) < 2:
            return False
        return parts

    def _inverse_name(self):
        """Try to revert the effect of :method:`._compute_name`."""
        for record in self:
            parts = self._get_inverse_name(record.name)
            record.write(
                {
                    "lastname": parts["lastname"],
                    "firstname": parts["firstname"],
                    "firstname2": parts["firstname2"],
                    "lastname2": parts["lastname2"],
                }
            )

    @api.model
    def _install_employee_lastnames(self):
        """Save names correctly in the database.
        Before installing the module, field ``name`` contains all full names.
        When installing it, this method parses those names and saves them
        correctly into the database. This can be called later too if needed.
        """
        # Find records with empty firstname and lastnames
        records = self.search(
            [("firstname", "=", False), ("lastname", "=", False)])

        # Force calculations there
        records._inverse_name()
        _logger.info("%d employees updated installing module.", len(records))

    @api.onchange("treatment", "firstname", "firstname2", "lastname", "lastname2", "married_name")
    def _onchange_firstname_lastname(self):
        if self.treatment:
            treatment = self.treatment
        else:
            treatment = ""

        if self.firstname or self.firstname2 or self.lastname or self.lastname2 or self.married_name:
            self.name = self._get_name_lastnames(
                treatment, self.lastname, self.firstname, self.firstname2, self.lastname2, self.married_name
            )

    # def _get_treatment(self, treatment):
    #     if treatment == 'senor':
    #         return 'Sr.'
    #     if treatment == 'senora':
    #         return 'Sra.'
    #     else:
    #         return ""
